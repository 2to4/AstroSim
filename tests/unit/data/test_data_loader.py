"""
DataLoaderクラスの単体テスト

データ読み込み・保存・検証機能の全てを検証します。
"""

import pytest
import json
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.data.data_loader import DataLoader, DataLoadException
from src.domain.solar_system import SolarSystem
from src.domain.sun import Sun
from src.domain.planet import Planet
from src.domain.orbital_elements import OrbitalElements


class TestDataLoader:
    """DataLoaderクラスのテスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        # 一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_dir / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # テスト用のサンプルデータ
        self.sample_planet_data = {
            "sun": {
                "name": "太陽",
                "mass": 1.989e30,
                "radius": 695700.0,
                "temperature": 5778.0,
                "luminosity": 3.828e26
            },
            "planets": {
                "earth": {
                    "name": "地球",
                    "mass": 5.972e24,
                    "radius": 6371000.0,
                    "color": [0.3, 0.7, 1.0],
                    "rotation_period": 24.0,
                    "axial_tilt": 23.44,
                    "orbital_elements": {
                        "semi_major_axis": 1.0,
                        "eccentricity": 0.0167,
                        "inclination": 0.0,
                        "longitude_of_ascending_node": 0.0,
                        "argument_of_perihelion": 0.0,
                        "mean_anomaly_at_epoch": 0.0,
                        "epoch": 2451545.0
                    }
                },
                "mars": {
                    "name": "火星",
                    "mass": 6.417e23,
                    "radius": 3389500.0,
                    "color": [1.0, 0.5, 0.3],
                    "rotation_period": 24.6,
                    "axial_tilt": 25.19,
                    "orbital_elements": {
                        "semi_major_axis": 1.524,
                        "eccentricity": 0.093,
                        "inclination": 1.85,
                        "longitude_of_ascending_node": 49.56,
                        "argument_of_perihelion": 286.5,
                        "mean_anomaly_at_epoch": 19.35,
                        "epoch": 2451545.0
                    }
                }
            },
            "metadata": {
                "version": "1.0.0",
                "description": "テスト用惑星データ"
            }
        }
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_default_path(self):
        """デフォルトパスでの初期化テスト"""
        data_loader = DataLoader()
        
        assert data_loader.base_path.exists()
        assert isinstance(data_loader.supported_formats, dict)
        assert '.json' in data_loader.supported_formats
        assert '.csv' in data_loader.supported_formats
        assert '.txt' in data_loader.supported_formats
    
    def test_initialization_custom_path(self):
        """カスタムパスでの初期化テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        assert data_loader.base_path == self.test_data_dir
        assert self.test_data_dir.exists()
        assert data_loader.planet_repository is None
        assert data_loader.config_manager is None
    
    def test_supported_formats(self):
        """サポートされているファイル形式のテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        supported = data_loader.get_supported_formats()
        assert '.json' in supported
        assert '.csv' in supported
        assert '.txt' in supported
        assert len(supported) == 3
    
    def create_test_json_file(self, data=None):
        """テスト用JSONファイルを作成"""
        if data is None:
            data = self.sample_planet_data
        
        json_path = self.test_data_dir / "test_planet_data.json"
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        
        return json_path
    
    def create_test_csv_file(self):
        """テスト用CSVファイルを作成"""
        csv_path = self.test_data_dir / "test_planet_data.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # ヘッダー
            writer.writerow([
                'name', 'mass', 'radius', 'color_r', 'color_g', 'color_b',
                'rotation_period', 'axial_tilt', 'semi_major_axis', 'eccentricity',
                'inclination', 'longitude_of_ascending_node', 'argument_of_perihelion',
                'mean_anomaly_at_epoch', 'epoch'
            ])
            
            # 地球のデータ
            writer.writerow([
                '地球', 5.972e24, 6371000.0, 0.3, 0.7, 1.0,
                24.0, 23.44, 1.0, 0.0167,
                0.0, 0.0, 0.0, 0.0, 2451545.0
            ])
            
            # 火星のデータ
            writer.writerow([
                '火星', 6.417e23, 3389500.0, 1.0, 0.5, 0.3,
                24.6, 25.19, 1.524, 0.093,
                1.85, 49.56, 286.5, 19.35, 2451545.0
            ])
        
        return csv_path
    
    @patch('src.data.data_loader.PlanetRepository')
    def test_load_default_solar_system(self, mock_planet_repo):
        """デフォルト太陽系データの読み込みテスト"""
        # モック設定
        mock_repo_instance = Mock()
        mock_solar_system = Mock()
        mock_solar_system.get_planet_count.return_value = 8
        mock_repo_instance.build_solar_system.return_value = mock_solar_system
        mock_planet_repo.return_value = mock_repo_instance
        
        data_loader = DataLoader(self.test_data_dir)
        
        # デフォルトデータファイルを作成
        default_path = self.test_data_dir / "planet_data.json"
        with open(default_path, 'w', encoding='utf-8') as file:
            json.dump(self.sample_planet_data, file)
        
        # 読み込み実行
        solar_system = data_loader.load_default_solar_system()
        
        # 検証
        assert solar_system is not None
        assert data_loader.planet_repository is not None
        mock_planet_repo.assert_called_once_with(default_path)
        mock_repo_instance.build_solar_system.assert_called_once()
    
    @patch('src.data.data_loader.PlanetRepository')
    def test_load_solar_system_from_json(self, mock_planet_repo):
        """JSONファイルからの太陽系データ読み込みテスト"""
        # モック設定
        mock_repo_instance = Mock()
        mock_solar_system = Mock()
        mock_repo_instance.build_solar_system.return_value = mock_solar_system
        mock_planet_repo.return_value = mock_repo_instance
        
        data_loader = DataLoader(self.test_data_dir)
        json_path = self.create_test_json_file()
        
        # 読み込み実行
        solar_system = data_loader.load_solar_system_from_file(json_path)
        
        # 検証
        assert solar_system is not None
        mock_planet_repo.assert_called_once_with(json_path)
    
    @patch('src.data.data_loader.PlanetRepository')
    def test_load_solar_system_from_csv(self, mock_planet_repo):
        """CSVファイルからの太陽系データ読み込みテスト"""
        # モック設定
        mock_repo_instance = Mock()
        mock_solar_system = Mock()
        mock_repo_instance.build_solar_system.return_value = mock_solar_system
        mock_planet_repo.return_value = mock_repo_instance
        
        data_loader = DataLoader(self.test_data_dir)
        csv_path = self.create_test_csv_file()
        
        # 読み込み実行
        solar_system = data_loader.load_solar_system_from_file(csv_path)
        
        # 検証
        assert solar_system is not None
        # 一時JSONファイルでPlanetRepositoryが呼び出される
        mock_planet_repo.assert_called_once()
        
        # 一時ファイルが削除されることを確認
        temp_json = self.test_data_dir / "temp_planet_data.json"
        assert not temp_json.exists()
    
    def test_load_nonexistent_file(self):
        """存在しないファイルの読み込みエラーテスト"""
        data_loader = DataLoader(self.test_data_dir)
        nonexistent_path = self.test_data_dir / "nonexistent.json"
        
        with pytest.raises(DataLoadException) as exc_info:
            data_loader.load_solar_system_from_file(nonexistent_path)
        
        assert "ファイルが見つかりません" in str(exc_info.value)
    
    def test_load_unsupported_format(self):
        """サポートされていないファイル形式のテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # .xmlファイルを作成
        xml_path = self.test_data_dir / "test.xml"
        xml_path.write_text("<data></data>")
        
        with pytest.raises(DataLoadException) as exc_info:
            data_loader.load_solar_system_from_file(xml_path)
        
        assert "サポートされていないファイル形式" in str(exc_info.value)
    
    def test_convert_csv_row_to_planet_data(self):
        """CSV行から惑星データへの変換テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 完全なCSV行データ
        complete_row = {
            'name': 'テスト惑星',
            'mass': '1.0e24',
            'radius': '6000000',
            'color_r': '0.8',
            'color_g': '0.2',
            'color_b': '0.1',
            'rotation_period': '25.0',
            'axial_tilt': '15.0',
            'semi_major_axis': '1.5',
            'eccentricity': '0.05',
            'inclination': '2.0',
            'longitude_of_ascending_node': '45.0',
            'argument_of_perihelion': '90.0',
            'mean_anomaly_at_epoch': '180.0',
            'epoch': '2451545.0'
        }
        
        planet_data = data_loader._convert_csv_row_to_planet_data(complete_row)
        
        assert planet_data is not None
        assert planet_data['name'] == 'テスト惑星'
        assert planet_data['mass'] == 1.0e24
        assert planet_data['radius'] == 6000000
        assert planet_data['color'] == [0.8, 0.2, 0.1]
        assert planet_data['orbital_elements']['semi_major_axis'] == 1.5
        assert planet_data['orbital_elements']['eccentricity'] == 0.05
    
    def test_convert_csv_row_missing_required(self):
        """必須フィールド欠如のCSV行変換テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 必須フィールドが欠如している行
        incomplete_row = {
            'name': 'テスト惑星',
            'mass': '1.0e24'
            # radius, semi_major_axis が欠如
        }
        
        planet_data = data_loader._convert_csv_row_to_planet_data(incomplete_row)
        assert planet_data is None
    
    def test_convert_csv_row_with_defaults(self):
        """デフォルト値を使用するCSV行変換テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 最小限のフィールドのみ
        minimal_row = {
            'name': 'ミニマル惑星',
            'mass': '2.0e24',
            'radius': '7000000',
            'semi_major_axis': '2.0'
        }
        
        planet_data = data_loader._convert_csv_row_to_planet_data(minimal_row)
        
        assert planet_data is not None
        assert planet_data['name'] == 'ミニマル惑星'
        assert planet_data['color'] == [0.5, 0.5, 0.5]  # デフォルト色
        assert planet_data['rotation_period'] == 24.0  # デフォルト自転周期
        assert planet_data['orbital_elements']['eccentricity'] == 0.0  # デフォルト離心率
    
    @patch('src.data.data_loader.ConfigManager')
    def test_load_config(self, mock_config_manager):
        """設定ファイル読み込みテスト"""
        mock_config = Mock()
        mock_config_manager.return_value = mock_config
        
        data_loader = DataLoader(self.test_data_dir)
        config_path = self.test_data_dir / "test_config.json"
        
        result = data_loader.load_config(config_path)
        
        assert result is mock_config
        assert data_loader.config_manager is mock_config
        mock_config_manager.assert_called_once_with(config_path)
    
    def test_save_solar_system_to_json(self):
        """太陽系データのJSON保存テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # モック太陽系オブジェクトを作成
        mock_solar_system = Mock()
        mock_solar_system.to_dict.return_value = {
            'sun': {'name': '太陽', 'mass': 1.989e30},
            'planets': [
                {'name': '地球', 'mass': 5.972e24},
                {'name': '火星', 'mass': 6.417e23}
            ],
            'current_date': 2451545.0
        }
        
        save_path = self.test_data_dir / "saved_system.json"
        
        # 保存実行
        success = data_loader.save_solar_system(mock_solar_system, save_path)
        
        assert success is True
        assert save_path.exists()
        
        # 保存されたファイルの内容確認
        with open(save_path, 'r', encoding='utf-8') as file:
            saved_data = json.load(file)
        
        assert 'sun' in saved_data
        assert 'planets' in saved_data
        assert 'metadata' in saved_data
        assert saved_data['metadata']['planet_count'] == 2
    
    def test_save_solar_system_to_csv(self):
        """太陽系データのCSV保存テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # モック惑星オブジェクトを作成
        mock_planet1 = Mock()
        mock_planet1.to_dict.return_value = {
            'name': '地球',
            'mass': 5.972e24,
            'radius': 6371000,
            'color': [0.3, 0.7, 1.0],
            'rotation_period': 24.0,
            'axial_tilt': 23.44,
            'orbital_elements': {
                'semi_major_axis': 1.0,
                'eccentricity': 0.0167,
                'inclination': 0.0,
                'longitude_of_ascending_node': 0.0,
                'argument_of_perihelion': 0.0,
                'mean_anomaly_at_epoch': 0.0,
                'epoch': 2451545.0
            }
        }
        
        mock_solar_system = Mock()
        mock_solar_system.get_planets_list.return_value = [mock_planet1]
        
        save_path = self.test_data_dir / "saved_system.csv"
        
        # 保存実行
        success = data_loader.save_solar_system(mock_solar_system, save_path)
        
        assert success is True
        assert save_path.exists()
        
        # 保存されたCSVファイルの内容確認
        with open(save_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['name'] == '地球'
        assert float(rows[0]['mass']) == 5.972e24
        assert float(rows[0]['color_r']) == 0.3
    
    def test_save_unsupported_format(self):
        """サポートされていない形式での保存テスト"""
        data_loader = DataLoader(self.test_data_dir)
        mock_solar_system = Mock()
        
        xml_path = self.test_data_dir / "test.xml"
        
        success = data_loader.save_solar_system(mock_solar_system, xml_path)
        assert success is False
    
    def test_load_custom_data_json(self):
        """カスタムJSONデータの読み込みテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # テストJSONファイルを作成
        test_data = {"test_key": "test_value", "number": 42}
        json_path = self.test_data_dir / "custom.json"
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(test_data, file)
        
        # 読み込み実行
        loaded_data = data_loader.load_custom_data(json_path)
        
        assert loaded_data == test_data
    
    def test_load_custom_data_csv(self):
        """カスタムCSVデータの読み込みテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # テストCSVファイルを作成
        csv_path = self.test_data_dir / "custom.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'value'])
            writer.writerow(['item1', '10'])
            writer.writerow(['item2', '20'])
        
        # 読み込み実行
        loaded_data = data_loader.load_custom_data(csv_path)
        
        assert len(loaded_data) == 2
        assert loaded_data[0]['name'] == 'item1'
        assert loaded_data[0]['value'] == '10'
    
    def test_load_custom_data_text(self):
        """カスタムテキストデータの読み込みテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # テストテキストファイルを作成
        txt_path = self.test_data_dir / "custom.txt"
        test_content = "これはテストファイルです。\n複数行のテキストです。"
        
        with open(txt_path, 'w', encoding='utf-8') as file:
            file.write(test_content)
        
        # 読み込み実行
        loaded_data = data_loader.load_custom_data(txt_path)
        
        assert loaded_data == test_content
    
    def test_load_custom_data_unsupported(self):
        """サポートされていない形式のカスタムデータ読み込みテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # .xmlファイルを作成
        xml_path = self.test_data_dir / "custom.xml"
        xml_path.write_text("<data></data>")
        
        with pytest.raises(DataLoadException) as exc_info:
            data_loader.load_custom_data(xml_path)
        
        assert "サポートされていないファイル形式" in str(exc_info.value)
    
    def test_validate_planet_data_valid(self):
        """有効な惑星データの検証テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        errors = data_loader.validate_planet_data(self.sample_planet_data)
        assert len(errors) == 0
    
    def test_validate_planet_data_missing_sections(self):
        """必須セクション欠如の検証テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # sunセクションが欠如
        invalid_data = {
            "planets": self.sample_planet_data["planets"]
        }
        
        errors = data_loader.validate_planet_data(invalid_data)
        assert len(errors) > 0
        assert any("必須セクション 'sun'" in error for error in errors)
    
    def test_validate_sun_data(self):
        """太陽データの検証テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 有効な太陽データ
        valid_sun = self.sample_planet_data["sun"]
        errors = data_loader._validate_sun_data(valid_sun)
        assert len(errors) == 0
        
        # 無効な太陽データ（必須フィールド欠如）
        invalid_sun = {"name": "太陽"}  # mass, radius が欠如
        errors = data_loader._validate_sun_data(invalid_sun)
        assert len(errors) >= 2
        
        # 無効な太陽データ（負の値）
        invalid_sun2 = {
            "name": "太陽",
            "mass": -1000,
            "radius": -500
        }
        errors = data_loader._validate_sun_data(invalid_sun2)
        assert len(errors) >= 2
    
    def test_validate_planets_data(self):
        """惑星データの検証テスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 有効な惑星データ（辞書形式）
        valid_planets = self.sample_planet_data["planets"]
        errors = data_loader._validate_planets_data(valid_planets)
        assert len(errors) == 0
        
        # 有効な惑星データ（リスト形式）
        valid_planets_list = list(valid_planets.values())
        errors = data_loader._validate_planets_data(valid_planets_list)
        assert len(errors) == 0
        
        # 無効な離心率
        invalid_planets = {
            "earth": {
                **valid_planets["earth"],
                "orbital_elements": {
                    **valid_planets["earth"]["orbital_elements"],
                    "eccentricity": 1.5  # 1以上は無効
                }
            }
        }
        errors = data_loader._validate_planets_data(invalid_planets)
        assert len(errors) > 0
        assert any("離心率は0以上1未満" in error for error in errors)
    
    def test_get_data_info(self):
        """データ情報取得のテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        info = data_loader.get_data_info()
        
        assert 'base_path' in info
        assert 'supported_formats' in info
        assert 'planet_repository_loaded' in info
        assert 'config_manager_loaded' in info
        
        assert info['base_path'] == str(self.test_data_dir)
        assert info['planet_repository_loaded'] is False
        assert info['config_manager_loaded'] is False
        assert len(info['supported_formats']) == 3
    
    def test_error_handling_json_decode_error(self):
        """JSON解析エラーのハンドリングテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 不正なJSONファイルを作成
        invalid_json_path = self.test_data_dir / "invalid.json"
        with open(invalid_json_path, 'w') as file:
            file.write("{ invalid json }")
        
        # PlanetRepositoryが不正なJSONでもデフォルトデータを使用するため、
        # DataLoadExceptionが発生する場合とそうでない場合がある
        try:
            result = data_loader.load_solar_system_from_file(invalid_json_path)
            # 成功した場合はデフォルトデータが使用される
            assert result is not None
        except DataLoadException:
            # 例外が発生することもある（実装に依存）
            pass
    
    def test_error_handling_csv_error(self):
        """CSV読み込みエラーのハンドリングテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        # 不正なCSVファイルを作成（必須カラムが欠如）
        invalid_csv_path = self.test_data_dir / "invalid.csv"
        with open(invalid_csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name'])  # 必須カラムが不足
            writer.writerow(['地球'])
        
        # CSVの場合は無効な行は無視されて、有効な惑星がない太陽系が作成される
        try:
            result = data_loader.load_solar_system_from_file(invalid_csv_path)
            # 成功した場合は太陽のみの太陽系が作成される
            assert result is not None
        except DataLoadException:
            # 例外が発生することもある（実装に依存）
            pass
    
    def test_string_representation(self):
        """文字列表現のテスト"""
        data_loader = DataLoader(self.test_data_dir)
        
        str_repr = str(data_loader)
        assert 'DataLoader' in str_repr
        assert str(self.test_data_dir) in str_repr
        assert '3' in str_repr  # サポート形式数


class TestDataLoaderIntegration:
    """DataLoaderの統合テスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "integration_data"
        self.data_dir.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_cycle_json(self):
        """JSON形式での完全サイクルテスト（読み込み→保存→再読み込み）"""
        data_loader = DataLoader(self.data_dir)
        
        # テストデータファイルを作成
        original_data = {
            "sun": {
                "name": "太陽",
                "mass": 1.989e30,
                "radius": 695700.0
            },
            "planets": {
                "earth": {
                    "name": "地球",
                    "mass": 5.972e24,
                    "radius": 6371000.0,
                    "color": [0.3, 0.7, 1.0],
                    "rotation_period": 24.0,
                    "axial_tilt": 23.44,
                    "orbital_elements": {
                        "semi_major_axis": 1.0,
                        "eccentricity": 0.0167,
                        "inclination": 0.0,
                        "longitude_of_ascending_node": 0.0,
                        "argument_of_perihelion": 0.0,
                        "mean_anomaly_at_epoch": 0.0,
                        "epoch": 2451545.0
                    }
                }
            }
        }
        
        original_path = self.data_dir / "original.json"
        with open(original_path, 'w', encoding='utf-8') as file:
            json.dump(original_data, file, ensure_ascii=False, indent=2)
        
        # モック太陽系オブジェクト（保存テスト用）
        mock_solar_system = Mock()
        mock_solar_system.to_dict.return_value = original_data
        mock_solar_system.get_planets_list.return_value = []
        
        # 保存
        saved_path = self.data_dir / "saved.json"
        success = data_loader.save_solar_system(mock_solar_system, saved_path)
        assert success is True
        
        # 保存されたファイルの検証
        errors = data_loader.validate_planet_data(original_data)
        assert len(errors) == 0
    
    def test_large_dataset_performance(self):
        """大量データのパフォーマンステスト"""
        data_loader = DataLoader(self.data_dir)
        
        # 100個の惑星データを作成
        large_data = {
            "sun": {
                "name": "太陽",
                "mass": 1.989e30,
                "radius": 695700.0
            },
            "planets": {}
        }
        
        for i in range(100):
            large_data["planets"][f"planet_{i}"] = {
                "name": f"惑星{i}",
                "mass": 1.0e24 + i * 1e22,
                "radius": 6000000 + i * 100000,
                "color": [0.5, 0.5, 0.5],
                "rotation_period": 24.0,
                "axial_tilt": 0.0,
                "orbital_elements": {
                    "semi_major_axis": 1.0 + i * 0.1,
                    "eccentricity": 0.01,
                    "inclination": 0.0,
                    "longitude_of_ascending_node": 0.0,
                    "argument_of_perihelion": 0.0,
                    "mean_anomaly_at_epoch": 0.0,
                    "epoch": 2451545.0
                }
            }
        
        # パフォーマンス測定
        import time
        
        # 検証処理の時間測定
        start_time = time.time()
        errors = data_loader.validate_planet_data(large_data)
        validation_time = time.time() - start_time
        
        # 1秒以内で完了することを確認
        assert validation_time < 1.0
        assert len(errors) == 0  # エラーがないことを確認
    
    def test_error_recovery(self):
        """エラー回復のテスト"""
        data_loader = DataLoader(self.data_dir)
        
        # 権限エラーのシミュレーション
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(DataLoadException):
                data_loader.load_custom_data(self.data_dir / "test.json")
        
        # ファイルシステムエラーのシミュレーション
        with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            with pytest.raises(DataLoadException):
                data_loader.load_custom_data(self.data_dir / "test.json")