"""
惑星データリポジトリクラスの実装

惑星データの永続化、読み込み、保存を管理します。
JSONファイルベースの実装とカスタムデータ対応。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.domain.orbital_elements import OrbitalElements
from src.domain.planet import Planet
from src.domain.sun import Sun
from src.domain.solar_system import SolarSystem


class PlanetRepository:
    """
    惑星データの永続化を管理するクラス
    
    JSONファイルからの惑星データ読み込み、
    カスタムデータの保存、太陽系オブジェクトの構築を行います。
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        惑星リポジトリの初期化
        
        Args:
            data_path: データファイルのパス（Noneの場合はデフォルト使用）
        """
        # データファイルパスの設定
        if data_path is None:
            self.data_path = Path(__file__).parent / "planet_data.json"
        else:
            self.data_path = data_path
        
        # データストレージ
        self._planet_data: Dict[str, Dict[str, Any]] = {}
        self._sun_data: Optional[Dict[str, Any]] = None
        self._metadata: Dict[str, Any] = {}
        
        # ロガー設定
        self.logger = logging.getLogger(__name__)
        
        # データ読み込み
        self._initialize_default_data()
        if self.data_path.exists():
            self._load_data()
        else:
            self.logger.warning(f"データファイルが見つかりません: {self.data_path}")
            self._create_default_data_file()
    
    def _initialize_default_data(self) -> None:
        """デフォルトの太陽系データを初期化"""
        # 太陽データ
        self._sun_data = {
            "name": "太陽",
            "mass": 1.989e30,  # kg
            "radius": 695700.0,  # km
            "temperature": 5778.0,  # K
            "luminosity": 3.828e26  # W
        }
        
        # 惑星データ（実際の太陽系データ）
        self._planet_data = {
            "水星": {
                "name": "水星",
                "mass": 3.301e23,  # kg
                "radius": 2439.7,  # km
                "color": [0.7, 0.7, 0.7],  # 灰色
                "rotation_period": 1407.6,  # 時間
                "axial_tilt": 0.034,  # 度
                "orbital_elements": {
                    "semi_major_axis": 0.387098,  # AU
                    "eccentricity": 0.205630,
                    "inclination": 7.005,  # 度
                    "longitude_of_ascending_node": 48.331,
                    "argument_of_perihelion": 29.124,
                    "mean_anomaly_at_epoch": 174.796,
                    "epoch": 2451545.0  # J2000.0
                }
            },
            "金星": {
                "name": "金星",
                "mass": 4.867e24,  # kg
                "radius": 6051.8,  # km
                "color": [1.0, 0.8, 0.4],  # 金色
                "rotation_period": -5832.5,  # 時間（逆回転）
                "axial_tilt": 177.4,  # 度
                "orbital_elements": {
                    "semi_major_axis": 0.723332,  # AU
                    "eccentricity": 0.006772,
                    "inclination": 3.39458,
                    "longitude_of_ascending_node": 76.680,
                    "argument_of_perihelion": 54.884,
                    "mean_anomaly_at_epoch": 50.115,
                    "epoch": 2451545.0
                }
            },
            "地球": {
                "name": "地球",
                "mass": 5.972e24,  # kg
                "radius": 6371.0,  # km
                "color": [0.3, 0.7, 1.0],  # 青色
                "rotation_period": 23.9345,  # 時間
                "axial_tilt": 23.44,  # 度
                "orbital_elements": {
                    "semi_major_axis": 1.00000261,  # AU
                    "eccentricity": 0.01671123,
                    "inclination": 0.00001531,
                    "longitude_of_ascending_node": -11.26064,
                    "argument_of_perihelion": 102.93768,
                    "mean_anomaly_at_epoch": 100.46457,
                    "epoch": 2451545.0
                }
            },
            "火星": {
                "name": "火星",
                "mass": 6.417e23,  # kg
                "radius": 3389.5,  # km
                "color": [0.8, 0.3, 0.1],  # 赤色
                "rotation_period": 24.6229,  # 時間
                "axial_tilt": 25.19,  # 度
                "orbital_elements": {
                    "semi_major_axis": 1.52371034,  # AU
                    "eccentricity": 0.09339410,
                    "inclination": 1.84969142,
                    "longitude_of_ascending_node": 49.55953891,
                    "argument_of_perihelion": 286.50210865,
                    "mean_anomaly_at_epoch": 19.3870,
                    "epoch": 2451545.0
                }
            },
            "木星": {
                "name": "木星",
                "mass": 1.898e27,  # kg
                "radius": 69911.0,  # km
                "color": [0.9, 0.7, 0.4],  # オレンジ色
                "rotation_period": 9.9259,  # 時間
                "axial_tilt": 3.13,  # 度
                "orbital_elements": {
                    "semi_major_axis": 5.20288700,  # AU
                    "eccentricity": 0.04838624,
                    "inclination": 1.30439695,
                    "longitude_of_ascending_node": 100.47390909,
                    "argument_of_perihelion": 273.86740840,
                    "mean_anomaly_at_epoch": 20.020,
                    "epoch": 2451545.0
                }
            },
            "土星": {
                "name": "土星",
                "mass": 5.683e26,  # kg
                "radius": 58232.0,  # km
                "color": [0.9, 0.9, 0.6],  # 淡い黄色
                "rotation_period": 10.656,  # 時間
                "axial_tilt": 26.73,  # 度
                "orbital_elements": {
                    "semi_major_axis": 9.53667594,  # AU
                    "eccentricity": 0.05386179,
                    "inclination": 2.48599187,
                    "longitude_of_ascending_node": 113.66242448,
                    "argument_of_perihelion": 339.39164700,
                    "mean_anomaly_at_epoch": 317.020,
                    "epoch": 2451545.0
                }
            },
            "天王星": {
                "name": "天王星",
                "mass": 8.681e25,  # kg
                "radius": 25362.0,  # km
                "color": [0.4, 0.8, 0.9],  # シアン色
                "rotation_period": -17.2417,  # 時間（逆回転）
                "axial_tilt": 97.77,  # 度
                "orbital_elements": {
                    "semi_major_axis": 19.18916464,  # AU
                    "eccentricity": 0.04725744,
                    "inclination": 0.77263783,
                    "longitude_of_ascending_node": 74.01692503,
                    "argument_of_perihelion": 96.99856000,
                    "mean_anomaly_at_epoch": 142.238,
                    "epoch": 2451545.0
                }
            },
            "海王星": {
                "name": "海王星",
                "mass": 1.024e26,  # kg
                "radius": 24622.0,  # km
                "color": [0.2, 0.3, 0.8],  # 青色
                "rotation_period": 16.1187,  # 時間
                "axial_tilt": 28.32,  # 度
                "orbital_elements": {
                    "semi_major_axis": 30.06992276,  # AU
                    "eccentricity": 0.00859048,
                    "inclination": 1.77004347,
                    "longitude_of_ascending_node": 131.78422574,
                    "argument_of_perihelion": 276.33640000,
                    "mean_anomaly_at_epoch": 260.813,
                    "epoch": 2451545.0
                }
            }
        }
        
        # メタデータ
        self._metadata = {
            "version": "1.0.0",
            "description": "太陽系惑星データ（J2000.0エポック）",
            "created": datetime.now().isoformat(),
            "source": "NASA JPL惑星および月の軌道要素",
            "coordinate_system": "J2000.0黄道座標系"
        }
    
    def _load_data(self) -> None:
        """JSONファイルからデータを読み込み"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # データ構造を検証
            if not self._validate_data_structure(data):
                self.logger.error("データファイルの構造が不正です")
                return
            
            # データを読み込み
            self._sun_data = data.get('sun', self._sun_data)
            self._planet_data = data.get('planets', self._planet_data)
            self._metadata = data.get('metadata', self._metadata)
            
            self.logger.info(f"データファイルを読み込みました: {self.data_path}")
            self.logger.info(f"惑星数: {len(self._planet_data)}")
            
        except FileNotFoundError:
            self.logger.error(f"データファイルが見つかりません: {self.data_path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSONファイルの解析エラー: {e}")
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
    
    def _validate_data_structure(self, data: Dict[str, Any]) -> bool:
        """データ構造の妥当性を検証"""
        required_keys = ['sun', 'planets', 'metadata']
        
        # 必須キーの存在確認
        for key in required_keys:
            if key not in data:
                self.logger.error(f"必須キー '{key}' が見つかりません")
                return False
        
        # 太陽データの検証
        sun_data = data['sun']
        sun_required = ['name', 'mass', 'radius']
        for key in sun_required:
            if key not in sun_data:
                self.logger.error(f"太陽データに必須キー '{key}' が見つかりません")
                return False
        
        # 惑星データの検証
        planets_data = data['planets']
        if not isinstance(planets_data, dict):
            self.logger.error("惑星データは辞書形式である必要があります")
            return False
        
        planet_required = ['name', 'mass', 'radius', 'orbital_elements']
        orbital_required = ['semi_major_axis', 'eccentricity', 'inclination']
        
        for planet_name, planet_data in planets_data.items():
            for key in planet_required:
                if key not in planet_data:
                    self.logger.error(f"惑星 '{planet_name}' に必須キー '{key}' が見つかりません")
                    return False
            
            # 軌道要素の検証
            orbital_elements = planet_data['orbital_elements']
            for key in orbital_required:
                if key not in orbital_elements:
                    self.logger.error(f"惑星 '{planet_name}' の軌道要素に必須キー '{key}' が見つかりません")
                    return False
        
        return True
    
    def _create_default_data_file(self) -> None:
        """デフォルトデータファイルを作成"""
        try:
            # ディレクトリを作成
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            
            # データ構造を作成
            data = {
                'sun': self._sun_data,
                'planets': self._planet_data,
                'metadata': self._metadata
            }
            
            # ファイルに保存
            with open(self.data_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"デフォルトデータファイルを作成しました: {self.data_path}")
            
        except Exception as e:
            self.logger.error(f"デフォルトデータファイル作成エラー: {e}")
    
    def get_all_planets(self) -> List[Dict[str, Any]]:
        """
        全惑星データを取得
        
        Returns:
            惑星データのリスト
        """
        return list(self._planet_data.values())
    
    def get_planet_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        名前で惑星データを取得
        
        Args:
            name: 惑星名
            
        Returns:
            惑星データ（見つからない場合はNone）
        """
        return self._planet_data.get(name)
    
    def get_sun_data(self) -> Optional[Dict[str, Any]]:
        """
        太陽データを取得
        
        Returns:
            太陽データ
        """
        return self._sun_data
    
    def get_planet_names(self) -> List[str]:
        """
        惑星名のリストを取得
        
        Returns:
            惑星名のリスト
        """
        return list(self._planet_data.keys())
    
    def build_solar_system(self) -> SolarSystem:
        """
        データからSolarSystemオブジェクトを構築
        
        Returns:
            構築された太陽系オブジェクト
        """
        solar_system = SolarSystem()
        
        # 太陽を追加
        if self._sun_data:
            sun = Sun(
                name=self._sun_data['name'],
                mass=self._sun_data['mass'],
                radius=self._sun_data['radius'],
                temperature=self._sun_data.get('temperature', 5778.0),
                luminosity=self._sun_data.get('luminosity', 3.828e26)
            )
            solar_system.add_celestial_body(sun)
        
        # 惑星を追加
        for planet_data in self._planet_data.values():
            planet = self._build_planet_from_data(planet_data)
            if planet:
                solar_system.add_celestial_body(planet)
        
        return solar_system
    
    def _build_planet_from_data(self, planet_data: Dict[str, Any]) -> Optional[Planet]:
        """データから惑星オブジェクトを構築"""
        try:
            # 軌道要素を構築
            orbital_data = planet_data['orbital_elements']
            orbital_elements = OrbitalElements(
                semi_major_axis=orbital_data['semi_major_axis'],
                eccentricity=orbital_data['eccentricity'],
                inclination=orbital_data['inclination'],
                longitude_of_ascending_node=orbital_data['longitude_of_ascending_node'],
                argument_of_perihelion=orbital_data['argument_of_perihelion'],
                mean_anomaly_at_epoch=orbital_data['mean_anomaly_at_epoch'],
                epoch=orbital_data['epoch']
            )
            
            # 惑星を構築
            planet = Planet(
                name=planet_data['name'],
                mass=planet_data['mass'],
                radius=planet_data['radius'],
                orbital_elements=orbital_elements,
                color=tuple(planet_data['color']),
                texture_path=planet_data.get('texture_path'),
                rotation_period=planet_data.get('rotation_period', 24.0),
                axial_tilt=planet_data.get('axial_tilt', 0.0)
            )
            
            return planet
            
        except Exception as e:
            self.logger.error(f"惑星 '{planet_data.get('name', '不明')}' の構築エラー: {e}")
            return None
    
    def save_custom_data(self, data: Dict[str, Any], backup: bool = True) -> bool:
        """
        カスタムデータを保存
        
        Args:
            data: 保存するデータ
            backup: バックアップを作成するか
            
        Returns:
            保存成功したかどうか
        """
        try:
            # バックアップ作成
            if backup and self.data_path.exists():
                backup_path = self.data_path.with_suffix('.bak')
                backup_path.write_bytes(self.data_path.read_bytes())
                self.logger.info(f"バックアップを作成しました: {backup_path}")
            
            # データ検証
            if not self._validate_data_structure(data):
                self.logger.error("保存データの構造が不正です")
                return False
            
            # ファイルに保存
            with open(self.data_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            
            # 内部データを更新
            self._sun_data = data.get('sun', self._sun_data)
            self._planet_data = data.get('planets', self._planet_data)
            self._metadata = data.get('metadata', self._metadata)
            
            self.logger.info(f"カスタムデータを保存しました: {self.data_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"データ保存エラー: {e}")
            return False
    
    def add_planet(self, planet_data: Dict[str, Any]) -> bool:
        """
        新しい惑星データを追加
        
        Args:
            planet_data: 惑星データ
            
        Returns:
            追加成功したかどうか
        """
        planet_name = planet_data.get('name')
        if not planet_name:
            self.logger.error("惑星名が指定されていません")
            return False
        
        if planet_name in self._planet_data:
            self.logger.warning(f"惑星 '{planet_name}' は既に存在します")
            return False
        
        # 必須データの検証
        required_keys = ['name', 'mass', 'radius', 'orbital_elements']
        for key in required_keys:
            if key not in planet_data:
                self.logger.error(f"必須キー '{key}' が見つかりません")
                return False
        
        # 内部データに追加
        self._planet_data[planet_name] = planet_data
        
        # ファイルに保存
        data = {
            'sun': self._sun_data,
            'planets': self._planet_data,
            'metadata': self._metadata
        }
        
        return self.save_custom_data(data, backup=True)
    
    def remove_planet(self, planet_name: str) -> bool:
        """
        惑星データを削除
        
        Args:
            planet_name: 削除する惑星名
            
        Returns:
            削除成功したかどうか
        """
        if planet_name not in self._planet_data:
            self.logger.warning(f"惑星 '{planet_name}' が見つかりません")
            return False
        
        # 内部データから削除
        del self._planet_data[planet_name]
        
        # ファイルに保存
        data = {
            'sun': self._sun_data,
            'planets': self._planet_data,
            'metadata': self._metadata
        }
        
        self.logger.info(f"惑星 '{planet_name}' を削除しました")
        return self.save_custom_data(data, backup=True)
    
    def get_metadata(self) -> Dict[str, Any]:
        """メタデータを取得"""
        return self._metadata.copy()
    
    def get_data_info(self) -> Dict[str, Any]:
        """データ情報を取得"""
        return {
            'data_path': str(self.data_path),
            'planet_count': len(self._planet_data),
            'has_sun': self._sun_data is not None,
            'metadata': self._metadata,
            'file_exists': self.data_path.exists(),
            'file_size': self.data_path.stat().st_size if self.data_path.exists() else 0
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"PlanetRepository ({len(self._planet_data)}惑星, パス: {self.data_path})"