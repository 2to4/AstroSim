"""
データローダークラスの実装

各種データファイルの読み込み、フォーマット変換、
データ検証などを統合的に管理します。
"""

import json
import csv
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

from src.data.planet_repository import PlanetRepository
from src.data.config_manager import ConfigManager
from src.domain.solar_system import SolarSystem


class DataLoadException(Exception):
    """データ読み込み例外"""
    pass


class DataLoader:
    """
    データ読み込みを統合管理するクラス
    
    惑星データ、設定ファイル、カスタムデータなどの
    読み込みと検証を行います。
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        データローダーの初期化
        
        Args:
            base_path: データファイルのベースパス
        """
        # ベースパスの設定
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent / "data"
        else:
            self.base_path = base_path
        
        # ベースディレクトリを作成
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # コンポーネント
        self.planet_repository: Optional[PlanetRepository] = None
        self.config_manager: Optional[ConfigManager] = None
        
        # ロガー設定
        self.logger = logging.getLogger(__name__)
        
        # サポートされるファイル形式
        self.supported_formats = {
            '.json': self._load_json,
            '.csv': self._load_csv,
            '.txt': self._load_text
        }
    
    def load_default_solar_system(self) -> SolarSystem:
        """
        デフォルトの太陽系データを読み込み
        
        Returns:
            構築された太陽系オブジェクト
            
        Raises:
            DataLoadException: データ読み込みエラー
        """
        try:
            # 惑星リポジトリを初期化
            default_data_path = self.base_path / "planet_data.json"
            self.planet_repository = PlanetRepository(default_data_path)
            
            # 太陽系オブジェクトを構築
            solar_system = self.planet_repository.build_solar_system()
            
            # 初期位置を計算（J2000.0エポック: JD 2451545.0）
            julian_date_j2000 = 2451545.0
            solar_system.update_all_positions(julian_date_j2000)
            
            self.logger.info(f"デフォルト太陽系データを読み込みました ({solar_system.get_planet_count()}惑星)")
            return solar_system
            
        except Exception as e:
            error_msg = f"デフォルト太陽系データの読み込みエラー: {e}"
            self.logger.error(error_msg)
            raise DataLoadException(error_msg)
    
    def load_solar_system_from_file(self, file_path: Union[str, Path]) -> SolarSystem:
        """
        ファイルから太陽系データを読み込み
        
        Args:
            file_path: データファイルのパス
            
        Returns:
            構築された太陽系オブジェクト
            
        Raises:
            DataLoadException: データ読み込みエラー
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DataLoadException(f"ファイルが見つかりません: {file_path}")
        
        try:
            # ファイル形式に応じて読み込み
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.json':
                return self._load_solar_system_from_json(file_path)
            elif file_extension == '.csv':
                return self._load_solar_system_from_csv(file_path)
            else:
                raise DataLoadException(f"サポートされていないファイル形式: {file_extension}")
                
        except Exception as e:
            error_msg = f"太陽系データ読み込みエラー: {e}"
            self.logger.error(error_msg)
            raise DataLoadException(error_msg)
    
    def _load_solar_system_from_json(self, file_path: Path) -> SolarSystem:
        """JSONファイルから太陽系データを読み込み"""
        self.planet_repository = PlanetRepository(file_path)
        return self.planet_repository.build_solar_system()
    
    def _load_solar_system_from_csv(self, file_path: Path) -> SolarSystem:
        """CSVファイルから太陽系データを読み込み"""
        try:
            planets_data = {}
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    planet_data = self._convert_csv_row_to_planet_data(row)
                    if planet_data:
                        planets_data[planet_data['name']] = planet_data
            
            # JSON形式に変換してPlanetRepositoryで処理
            json_data = {
                'sun': {
                    'name': '太陽',
                    'mass': 1.989e30,
                    'radius': 695700.0,
                    'temperature': 5778.0,
                    'luminosity': 3.828e26
                },
                'planets': planets_data,
                'metadata': {
                    'version': '1.0.0',
                    'source': f'CSVファイル: {file_path.name}',
                    'loaded': datetime.now().isoformat()
                }
            }
            
            # 一時的なJSONファイルを作成してPlanetRepositoryで読み込み
            temp_json_path = self.base_path / "temp_planet_data.json"
            
            with open(temp_json_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=2)
            
            self.planet_repository = PlanetRepository(temp_json_path)
            solar_system = self.planet_repository.build_solar_system()
            
            # 一時ファイルを削除
            temp_json_path.unlink()
            
            return solar_system
            
        except Exception as e:
            raise DataLoadException(f"CSV読み込みエラー: {e}")
    
    def _convert_csv_row_to_planet_data(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """CSV行を惑星データに変換"""
        try:
            # 必須フィールドの確認
            required_fields = ['name', 'mass', 'radius', 'semi_major_axis']
            for field in required_fields:
                if field not in row or not row[field]:
                    self.logger.warning(f"必須フィールド '{field}' が見つかりません")
                    return None
            
            # 数値変換
            def safe_float(value: str, default: float = 0.0) -> float:
                try:
                    return float(value) if value else default
                except ValueError:
                    return default
            
            # 色データの処理
            color = [0.5, 0.5, 0.5]  # デフォルト
            if 'color_r' in row and 'color_g' in row and 'color_b' in row:
                color = [
                    safe_float(row['color_r'], 0.5),
                    safe_float(row['color_g'], 0.5),
                    safe_float(row['color_b'], 0.5)
                ]
            
            # 惑星データを構築
            planet_data = {
                'name': row['name'],
                'mass': safe_float(row['mass']),
                'radius': safe_float(row['radius']),
                'color': color,
                'rotation_period': safe_float(row.get('rotation_period', '24.0'), 24.0),
                'axial_tilt': safe_float(row.get('axial_tilt', '0.0'), 0.0),
                'orbital_elements': {
                    'semi_major_axis': safe_float(row['semi_major_axis']),
                    'eccentricity': safe_float(row.get('eccentricity', '0.0'), 0.0),
                    'inclination': safe_float(row.get('inclination', '0.0'), 0.0),
                    'longitude_of_ascending_node': safe_float(row.get('longitude_of_ascending_node', '0.0'), 0.0),
                    'argument_of_perihelion': safe_float(row.get('argument_of_perihelion', '0.0'), 0.0),
                    'mean_anomaly_at_epoch': safe_float(row.get('mean_anomaly_at_epoch', '0.0'), 0.0),
                    'epoch': safe_float(row.get('epoch', '2451545.0'), 2451545.0)
                }
            }
            
            return planet_data
            
        except Exception as e:
            self.logger.error(f"CSV行変換エラー: {e}")
            return None
    
    def load_config(self, config_path: Optional[Path] = None) -> ConfigManager:
        """
        設定ファイルを読み込み
        
        Args:
            config_path: 設定ファイルのパス
            
        Returns:
            設定管理オブジェクト
        """
        try:
            self.config_manager = ConfigManager(config_path)
            self.logger.info("設定ファイルを読み込みました")
            return self.config_manager
            
        except Exception as e:
            error_msg = f"設定読み込みエラー: {e}"
            self.logger.error(error_msg)
            raise DataLoadException(error_msg)
    
    def save_solar_system(self, solar_system: SolarSystem, file_path: Union[str, Path]) -> bool:
        """
        太陽系データをファイルに保存
        
        Args:
            solar_system: 太陽系オブジェクト
            file_path: 保存先ファイルパス
            
        Returns:
            保存成功したかどうか
        """
        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.json':
                return self._save_solar_system_to_json(solar_system, file_path)
            elif file_extension == '.csv':
                return self._save_solar_system_to_csv(solar_system, file_path)
            else:
                self.logger.error(f"サポートされていない保存形式: {file_extension}")
                return False
                
        except Exception as e:
            self.logger.error(f"太陽系データ保存エラー: {e}")
            return False
    
    def _save_solar_system_to_json(self, solar_system: SolarSystem, file_path: Path) -> bool:
        """太陽系データをJSONファイルに保存"""
        try:
            # 太陽系データを辞書に変換
            data = solar_system.to_dict()
            
            # メタデータを追加
            save_data = {
                'sun': data.get('sun'),
                'planets': data.get('planets', []),
                'metadata': {
                    'version': '1.0.0',
                    'saved': datetime.now().isoformat(),
                    'planet_count': len(data.get('planets', [])),
                    'current_date': data.get('current_date', 0.0)
                }
            }
            
            # ファイルに保存
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(save_data, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"太陽系データをJSONに保存しました: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON保存エラー: {e}")
            return False
    
    def _save_solar_system_to_csv(self, solar_system: SolarSystem, file_path: Path) -> bool:
        """太陽系データをCSVファイルに保存"""
        try:
            fieldnames = [
                'name', 'mass', 'radius', 'color_r', 'color_g', 'color_b',
                'rotation_period', 'axial_tilt', 'semi_major_axis', 'eccentricity',
                'inclination', 'longitude_of_ascending_node', 'argument_of_perihelion',
                'mean_anomaly_at_epoch', 'epoch'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                # 惑星データを行として書き込み
                for planet in solar_system.get_planets_list():
                    planet_dict = planet.to_dict()
                    orbital_elements = planet_dict['orbital_elements']
                    
                    row = {
                        'name': planet_dict['name'],
                        'mass': planet_dict['mass'],
                        'radius': planet_dict['radius'],
                        'color_r': planet_dict['color'][0],
                        'color_g': planet_dict['color'][1],
                        'color_b': planet_dict['color'][2],
                        'rotation_period': planet_dict['rotation_period'],
                        'axial_tilt': planet_dict['axial_tilt'],
                        'semi_major_axis': orbital_elements['semi_major_axis'],
                        'eccentricity': orbital_elements['eccentricity'],
                        'inclination': orbital_elements['inclination'],
                        'longitude_of_ascending_node': orbital_elements['longitude_of_ascending_node'],
                        'argument_of_perihelion': orbital_elements['argument_of_perihelion'],
                        'mean_anomaly_at_epoch': orbital_elements['mean_anomaly_at_epoch'],
                        'epoch': orbital_elements['epoch']
                    }
                    
                    writer.writerow(row)
            
            self.logger.info(f"太陽系データをCSVに保存しました: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {e}")
            return False
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    def _load_csv(self, file_path: Path) -> List[Dict[str, str]]:
        """CSVファイルを読み込み"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data
    
    def _load_text(self, file_path: Path) -> str:
        """テキストファイルを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def load_custom_data(self, file_path: Union[str, Path]) -> Any:
        """
        カスタムデータファイルを読み込み
        
        Args:
            file_path: ファイルパス
            
        Returns:
            読み込まれたデータ
            
        Raises:
            DataLoadException: データ読み込みエラー
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DataLoadException(f"ファイルが見つかりません: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise DataLoadException(f"サポートされていないファイル形式: {file_extension}")
        
        try:
            loader_func = self.supported_formats[file_extension]
            data = loader_func(file_path)
            
            self.logger.info(f"カスタムデータを読み込みました: {file_path}")
            return data
            
        except Exception as e:
            error_msg = f"カスタムデータ読み込みエラー: {e}"
            self.logger.error(error_msg)
            raise DataLoadException(error_msg)
    
    def validate_planet_data(self, data: Dict[str, Any]) -> List[str]:
        """
        惑星データの妥当性を検証
        
        Args:
            data: 検証するデータ
            
        Returns:
            エラーメッセージのリスト
        """
        errors = []
        
        try:
            # 基本構造の確認
            if not isinstance(data, dict):
                errors.append("データのルートオブジェクトが辞書ではありません")
                return errors
            
            # 必須セクションの確認
            required_sections = ['sun', 'planets']
            for section in required_sections:
                if section not in data:
                    errors.append(f"必須セクション '{section}' が見つかりません")
            
            # 太陽データの検証
            if 'sun' in data:
                sun_errors = self._validate_sun_data(data['sun'])
                errors.extend(sun_errors)
            
            # 惑星データの検証
            if 'planets' in data:
                planets_errors = self._validate_planets_data(data['planets'])
                errors.extend(planets_errors)
                
        except Exception as e:
            errors.append(f"データ検証中にエラーが発生しました: {e}")
        
        return errors
    
    def _validate_sun_data(self, sun_data: Dict[str, Any]) -> List[str]:
        """太陽データの検証"""
        errors = []
        
        required_fields = ['name', 'mass', 'radius']
        for field in required_fields:
            if field not in sun_data:
                errors.append(f"太陽データに必須フィールド '{field}' が見つかりません")
        
        # 数値範囲チェック
        if 'mass' in sun_data:
            mass = sun_data['mass']
            if not isinstance(mass, (int, float)) or mass <= 0:
                errors.append("太陽の質量は正の数値である必要があります")
        
        if 'radius' in sun_data:
            radius = sun_data['radius']
            if not isinstance(radius, (int, float)) or radius <= 0:
                errors.append("太陽の半径は正の数値である必要があります")
        
        return errors
    
    def _validate_planets_data(self, planets_data: Union[Dict, List]) -> List[str]:
        """惑星データの検証"""
        errors = []
        
        # 辞書形式またはリスト形式に対応
        if isinstance(planets_data, dict):
            planets_list = planets_data.values()
        elif isinstance(planets_data, list):
            planets_list = planets_data
        else:
            errors.append("惑星データは辞書またはリスト形式である必要があります")
            return errors
        
        required_fields = ['name', 'mass', 'radius', 'orbital_elements']
        orbital_required = ['semi_major_axis', 'eccentricity']
        
        for i, planet_data in enumerate(planets_list):
            planet_id = planet_data.get('name', f'惑星{i+1}')
            
            # 必須フィールドチェック
            for field in required_fields:
                if field not in planet_data:
                    errors.append(f"惑星 '{planet_id}' に必須フィールド '{field}' が見つかりません")
            
            # 軌道要素チェック
            if 'orbital_elements' in planet_data:
                orbital_elements = planet_data['orbital_elements']
                for field in orbital_required:
                    if field not in orbital_elements:
                        errors.append(f"惑星 '{planet_id}' の軌道要素に必須フィールド '{field}' が見つかりません")
                
                # 離心率チェック
                if 'eccentricity' in orbital_elements:
                    e = orbital_elements['eccentricity']
                    if not isinstance(e, (int, float)) or not (0 <= e < 1):
                        errors.append(f"惑星 '{planet_id}' の離心率は0以上1未満である必要があります")
        
        return errors
    
    def get_supported_formats(self) -> List[str]:
        """サポートされているファイル形式を取得"""
        return list(self.supported_formats.keys())
    
    def get_data_info(self) -> Dict[str, Any]:
        """データローダーの情報を取得"""
        info = {
            'base_path': str(self.base_path),
            'supported_formats': self.get_supported_formats(),
            'planet_repository_loaded': self.planet_repository is not None,
            'config_manager_loaded': self.config_manager is not None
        }
        
        if self.planet_repository:
            info['planet_data'] = self.planet_repository.get_data_info()
        
        if self.config_manager:
            info['config_data'] = self.config_manager.get_config_info()
        
        return info
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"DataLoader (ベースパス: {self.base_path}, 形式: {len(self.supported_formats)})"