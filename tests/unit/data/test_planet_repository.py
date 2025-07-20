"""
PlanetRepositoryクラスの単体テスト

惑星データの永続化・管理機能の全てを検証します。
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.data.planet_repository import PlanetRepository
from src.domain.solar_system import SolarSystem
from src.domain.planet import Planet
from src.domain.sun import Sun


class TestPlanetRepository:
    """PlanetRepositoryクラスのテスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        # 一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_path = self.temp_dir / "test_planet_data.json"
        
        # テスト用のサンプルデータ
        self.sample_data = {
            "sun": {
                "name": "太陽",
                "mass": 1.989e30,
                "radius": 695700.0,
                "temperature": 5778.0,
                "luminosity": 3.828e26
            },
            "planets": {
                "地球": {
                    "name": "地球",
                    "mass": 5.972e24,
                    "radius": 6371.0,
                    "color": [0.3, 0.7, 1.0],
                    "rotation_period": 23.9345,
                    "axial_tilt": 23.44,
                    "orbital_elements": {
                        "semi_major_axis": 1.00000261,
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
                    "mass": 6.417e23,
                    "radius": 3389.5,
                    "color": [0.8, 0.3, 0.1],
                    "rotation_period": 24.6229,
                    "axial_tilt": 25.19,
                    "orbital_elements": {
                        "semi_major_axis": 1.52371034,
                        "eccentricity": 0.09339410,
                        "inclination": 1.84969142,
                        "longitude_of_ascending_node": 49.55953891,
                        "argument_of_perihelion": 286.50210865,
                        "mean_anomaly_at_epoch": 19.3870,
                        "epoch": 2451545.0
                    }
                }
            },
            "metadata": {
                "version": "1.0.0",
                "description": "テスト用惑星データ",
                "created": "2024-01-01T00:00:00"
            }
        }
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_data_file(self, data=None):
        """テスト用データファイルを作成"""
        if data is None:
            data = self.sample_data
        
        with open(self.test_data_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    
    def test_initialization_with_existing_file(self):
        """既存ファイルがある場合の初期化テスト"""
        self.create_test_data_file()
        
        repo = PlanetRepository(self.test_data_path)
        
        assert repo.data_path == self.test_data_path
        assert repo._sun_data is not None
        assert len(repo._planet_data) == 2
        assert "地球" in repo._planet_data
        assert "火星" in repo._planet_data
    
    def test_initialization_without_file(self):
        """ファイルがない場合の初期化テスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # デフォルトデータが設定されることを確認
        assert repo._sun_data is not None
        assert len(repo._planet_data) >= 8  # デフォルトは8惑星
        assert repo._sun_data['name'] == "太陽"
        
        # デフォルトファイルが作成されることを確認
        assert self.test_data_path.exists()
    
    def test_initialization_default_path(self):
        """デフォルトパスでの初期化テスト"""
        with patch('pathlib.Path.exists', return_value=False):
            repo = PlanetRepository()
            
            # デフォルトパスが設定されることを確認
            assert 'planet_data.json' in str(repo.data_path)
            assert repo._sun_data is not None
            assert len(repo._planet_data) >= 8
    
    def test_default_data_initialization(self):
        """デフォルトデータ初期化のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 太陽データの確認
        sun_data = repo._sun_data
        assert sun_data['name'] == "太陽"
        assert sun_data['mass'] == 1.989e30
        assert sun_data['radius'] == 695700.0
        
        # 惑星データの確認（8惑星）
        expected_planets = ["水星", "金星", "地球", "火星", "木星", "土星", "天王星", "海王星"]
        for planet_name in expected_planets:
            assert planet_name in repo._planet_data
            planet_data = repo._planet_data[planet_name]
            assert 'mass' in planet_data
            assert 'radius' in planet_data
            assert 'orbital_elements' in planet_data
        
        # メタデータの確認
        metadata = repo._metadata
        assert 'version' in metadata
        assert 'description' in metadata
    
    def test_load_data_valid_file(self):
        """有効なデータファイルの読み込みテスト"""
        self.create_test_data_file()
        
        repo = PlanetRepository(self.test_data_path)
        
        # データが正しく読み込まれることを確認
        assert repo.get_planet_by_name("地球") is not None
        assert repo.get_planet_by_name("火星") is not None
        assert repo.get_sun_data()['name'] == "太陽"
    
    def test_load_data_invalid_json(self):
        """不正なJSONファイルの処理テスト"""
        # 不正なJSONファイルを作成
        with open(self.test_data_path, 'w') as file:
            file.write("{ invalid json }")
        
        # エラーが発生してもデフォルトデータが使用される
        repo = PlanetRepository(self.test_data_path)
        assert repo._sun_data is not None
        assert len(repo._planet_data) >= 8  # デフォルトデータ
    
    def test_validate_data_structure_valid(self):
        """有効なデータ構造の検証テスト"""
        repo = PlanetRepository(self.test_data_path)
        
        is_valid = repo._validate_data_structure(self.sample_data)
        assert is_valid is True
    
    def test_validate_data_structure_missing_keys(self):
        """必須キー欠如のデータ構造検証テスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 'sun'キーが欠如
        invalid_data = {
            "planets": self.sample_data["planets"],
            "metadata": self.sample_data["metadata"]
        }
        
        is_valid = repo._validate_data_structure(invalid_data)
        assert is_valid is False
    
    def test_validate_data_structure_invalid_sun(self):
        """無効な太陽データの検証テスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 太陽データに必須キーが欠如
        invalid_data = self.sample_data.copy()
        invalid_data["sun"] = {"name": "太陽"}  # mass, radius が欠如
        
        is_valid = repo._validate_data_structure(invalid_data)
        assert is_valid is False
    
    def test_validate_data_structure_invalid_planet(self):
        """無効な惑星データの検証テスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 惑星データに必須キーが欠如
        invalid_data = self.sample_data.copy()
        invalid_data["planets"]["地球"] = {
            "name": "地球",
            "mass": 5.972e24
            # radius, orbital_elements が欠如
        }
        
        is_valid = repo._validate_data_structure(invalid_data)
        assert is_valid is False
    
    def test_get_all_planets(self):
        """全惑星データ取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        planets = repo.get_all_planets()
        assert len(planets) == 2
        planet_names = [p['name'] for p in planets]
        assert "地球" in planet_names
        assert "火星" in planet_names
    
    def test_get_planet_by_name(self):
        """名前による惑星データ取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        # 存在する惑星
        earth = repo.get_planet_by_name("地球")
        assert earth is not None
        assert earth['name'] == "地球"
        assert earth['mass'] == 5.972e24
        
        # 存在しない惑星
        jupiter = repo.get_planet_by_name("木星")
        assert jupiter is None
    
    def test_get_sun_data(self):
        """太陽データ取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        sun_data = repo.get_sun_data()
        assert sun_data is not None
        assert sun_data['name'] == "太陽"
        assert sun_data['mass'] == 1.989e30
    
    def test_get_planet_names(self):
        """惑星名リスト取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        names = repo.get_planet_names()
        assert len(names) == 2
        assert "地球" in names
        assert "火星" in names
    
    @patch('src.data.planet_repository.Sun')
    @patch('src.data.planet_repository.Planet')
    @patch('src.data.planet_repository.SolarSystem')
    def test_build_solar_system(self, mock_solar_system, mock_planet, mock_sun):
        """太陽系オブジェクト構築のテスト"""
        # モックの設定
        mock_system_instance = Mock()
        mock_solar_system.return_value = mock_system_instance
        
        mock_sun_instance = Mock()
        mock_sun.return_value = mock_sun_instance
        
        mock_planet_instance = Mock()
        mock_planet.return_value = mock_planet_instance
        
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        # 太陽系構築
        solar_system = repo.build_solar_system()
        
        # 検証
        assert solar_system is mock_system_instance
        mock_solar_system.assert_called_once()
        mock_sun.assert_called_once()
        mock_system_instance.add_celestial_body.assert_called()
        
        # 太陽の作成パラメータ確認
        sun_call_args = mock_sun.call_args
        assert sun_call_args[1]['name'] == "太陽"
        assert sun_call_args[1]['mass'] == 1.989e30
    
    @patch('src.data.planet_repository.Planet')
    @patch('src.data.planet_repository.OrbitalElements')
    def test_build_planet_from_data(self, mock_orbital_elements, mock_planet):
        """惑星データからの惑星オブジェクト構築テスト"""
        # モックの設定
        mock_orbital_instance = Mock()
        mock_orbital_elements.return_value = mock_orbital_instance
        
        mock_planet_instance = Mock()
        mock_planet.return_value = mock_planet_instance
        
        repo = PlanetRepository(self.test_data_path)
        planet_data = self.sample_data["planets"]["地球"]
        
        # 惑星構築
        planet = repo._build_planet_from_data(planet_data)
        
        # 検証
        assert planet is mock_planet_instance
        mock_orbital_elements.assert_called_once()
        mock_planet.assert_called_once()
        
        # 軌道要素の作成パラメータ確認
        orbital_call_args = mock_orbital_elements.call_args
        assert orbital_call_args[1]['semi_major_axis'] == 1.00000261
        assert orbital_call_args[1]['eccentricity'] == 0.01671123
        
        # 惑星の作成パラメータ確認
        planet_call_args = mock_planet.call_args
        assert planet_call_args[1]['name'] == "地球"
        assert planet_call_args[1]['mass'] == 5.972e24
    
    def test_build_planet_from_invalid_data(self):
        """無効なデータからの惑星構築エラーテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 必須キーが欠如したデータ
        invalid_data = {
            "name": "無効惑星",
            "mass": 1.0e24
            # radius, orbital_elements が欠如
        }
        
        planet = repo._build_planet_from_data(invalid_data)
        assert planet is None
    
    def test_save_custom_data_valid(self):
        """有効なカスタムデータ保存のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        success = repo.save_custom_data(self.sample_data, backup=False)
        assert success is True
        
        # ファイルが作成されることを確認
        assert self.test_data_path.exists()
        
        # 内部データが更新されることを確認
        assert repo.get_planet_by_name("地球") is not None
        assert repo.get_planet_by_name("火星") is not None
    
    def test_save_custom_data_with_backup(self):
        """バックアップ付きカスタムデータ保存のテスト"""
        # 既存ファイルを作成
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        # 新しいデータで保存
        new_data = self.sample_data.copy()
        new_data["planets"]["金星"] = {
            "name": "金星",
            "mass": 4.867e24,
            "radius": 6051.8,
            "color": [1.0, 0.8, 0.4],
            "rotation_period": -5832.5,
            "axial_tilt": 177.4,
            "orbital_elements": {
                "semi_major_axis": 0.723332,
                "eccentricity": 0.006772,
                "inclination": 3.39458,
                "longitude_of_ascending_node": 76.680,
                "argument_of_perihelion": 54.884,
                "mean_anomaly_at_epoch": 50.115,
                "epoch": 2451545.0
            }
        }
        
        success = repo.save_custom_data(new_data, backup=True)
        assert success is True
        
        # バックアップファイルが作成されることを確認
        backup_path = self.test_data_path.with_suffix('.bak')
        assert backup_path.exists()
    
    def test_save_custom_data_invalid(self):
        """無効なカスタムデータ保存のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 無効なデータ（必須キー欠如）
        invalid_data = {
            "planets": self.sample_data["planets"]
            # sun, metadata が欠如
        }
        
        success = repo.save_custom_data(invalid_data)
        assert success is False
    
    def test_add_planet_valid(self):
        """有効な惑星追加のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        new_planet = {
            "name": "新惑星",
            "mass": 1.0e24,
            "radius": 5000.0,
            "color": [0.5, 0.5, 0.5],
            "rotation_period": 20.0,
            "axial_tilt": 10.0,
            "orbital_elements": {
                "semi_major_axis": 2.0,
                "eccentricity": 0.1,
                "inclination": 1.0,
                "longitude_of_ascending_node": 0.0,
                "argument_of_perihelion": 0.0,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 2451545.0
            }
        }
        
        success = repo.add_planet(new_planet)
        assert success is True
        
        # 追加された惑星を確認
        added_planet = repo.get_planet_by_name("新惑星")
        assert added_planet is not None
        assert added_planet['mass'] == 1.0e24
    
    def test_add_planet_missing_name(self):
        """名前なし惑星追加のエラーテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        invalid_planet = {
            "mass": 1.0e24,
            "radius": 5000.0
            # name が欠如
        }
        
        success = repo.add_planet(invalid_planet)
        assert success is False
    
    def test_add_planet_missing_required_keys(self):
        """必須キー欠如惑星追加のエラーテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        invalid_planet = {
            "name": "不完全惑星",
            "mass": 1.0e24
            # radius, orbital_elements が欠如
        }
        
        success = repo.add_planet(invalid_planet)
        assert success is False
    
    def test_add_planet_duplicate(self):
        """重複惑星追加のエラーテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        # 既存の惑星と同じ名前
        duplicate_planet = {
            "name": "地球",  # 既存
            "mass": 1.0e24,
            "radius": 5000.0,
            "orbital_elements": {
                "semi_major_axis": 2.0,
                "eccentricity": 0.1,
                "inclination": 1.0,
                "longitude_of_ascending_node": 0.0,
                "argument_of_perihelion": 0.0,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 2451545.0
            }
        }
        
        success = repo.add_planet(duplicate_planet)
        assert success is False
    
    def test_remove_planet_existing(self):
        """既存惑星削除のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        # 削除前の確認
        assert repo.get_planet_by_name("地球") is not None
        
        # 削除実行
        success = repo.remove_planet("地球")
        assert success is True
        
        # 削除後の確認
        assert repo.get_planet_by_name("地球") is None
        assert repo.get_planet_by_name("火星") is not None  # 他は残る
    
    def test_remove_planet_nonexistent(self):
        """存在しない惑星削除のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        success = repo.remove_planet("存在しない惑星")
        assert success is False
    
    def test_get_metadata(self):
        """メタデータ取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        metadata = repo.get_metadata()
        assert isinstance(metadata, dict)
        assert 'version' in metadata
        assert 'description' in metadata
        assert metadata['version'] == "1.0.0"
    
    def test_get_data_info(self):
        """データ情報取得のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        info = repo.get_data_info()
        
        assert 'data_path' in info
        assert 'planet_count' in info
        assert 'has_sun' in info
        assert 'metadata' in info
        assert 'file_exists' in info
        assert 'file_size' in info
        
        assert info['data_path'] == str(self.test_data_path)
        assert info['planet_count'] == 2
        assert info['has_sun'] is True
        assert info['file_exists'] is True
        assert info['file_size'] > 0
    
    def test_create_default_data_file(self):
        """デフォルトデータファイル作成のテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # ファイルが作成されることを確認
        assert self.test_data_path.exists()
        
        # ファイル内容の確認
        with open(self.test_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        assert 'sun' in data
        assert 'planets' in data
        assert 'metadata' in data
        assert len(data['planets']) >= 8  # 8惑星
    
    def test_string_representation(self):
        """文字列表現のテスト"""
        self.create_test_data_file()
        repo = PlanetRepository(self.test_data_path)
        
        str_repr = str(repo)
        assert 'PlanetRepository' in str_repr
        assert '2惑星' in str_repr
        assert str(self.test_data_path) in str_repr
    
    def test_error_handling_file_permissions(self):
        """ファイル権限エラーのハンドリングテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 読み取り専用ディレクトリのシミュレーション
        with patch('builtins.open', side_effect=PermissionError):
            success = repo.save_custom_data(self.sample_data)
            assert success is False
    
    def test_error_handling_json_encode_error(self):
        """JSON エンコードエラーのハンドリングテスト"""
        repo = PlanetRepository(self.test_data_path)
        
        # 循環参照を含むデータ（JSONエンコード不可）
        circular_data = self.sample_data.copy()
        circular_data['circular'] = circular_data  # 循環参照
        
        with patch('json.dump', side_effect=TypeError("Circular reference")):
            success = repo.save_custom_data(circular_data)
            assert success is False


class TestPlanetRepositoryIntegration:
    """PlanetRepositoryの統合テスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_path = self.temp_dir / "integration_test.json"
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_cycle_operations(self):
        """完全サイクル操作のテスト（作成→追加→削除→保存→読み込み）"""
        # 新規作成
        repo1 = PlanetRepository(self.data_path)
        original_count = len(repo1.get_planet_names())
        
        # 惑星追加
        new_planet = {
            "name": "テスト惑星",
            "mass": 1.0e24,
            "radius": 5000.0,
            "color": [0.8, 0.8, 0.8],
            "rotation_period": 25.0,
            "axial_tilt": 15.0,
            "orbital_elements": {
                "semi_major_axis": 3.0,
                "eccentricity": 0.2,
                "inclination": 5.0,
                "longitude_of_ascending_node": 45.0,
                "argument_of_perihelion": 90.0,
                "mean_anomaly_at_epoch": 180.0,
                "epoch": 2451545.0
            }
        }
        
        success = repo1.add_planet(new_planet)
        assert success is True
        assert len(repo1.get_planet_names()) == original_count + 1
        
        # 別のインスタンスで読み込み
        repo2 = PlanetRepository(self.data_path)
        assert len(repo2.get_planet_names()) == original_count + 1
        assert repo2.get_planet_by_name("テスト惑星") is not None
        
        # 惑星削除
        success = repo2.remove_planet("テスト惑星")
        assert success is True
        assert len(repo2.get_planet_names()) == original_count
        
        # さらに別のインスタンスで確認
        repo3 = PlanetRepository(self.data_path)
        assert len(repo3.get_planet_names()) == original_count
        assert repo3.get_planet_by_name("テスト惑星") is None
    
    def test_backup_and_recovery(self):
        """バックアップと復旧のテスト"""
        repo = PlanetRepository(self.data_path)
        
        # 初期データを保存
        initial_data = {
            "sun": repo.get_sun_data(),
            "planets": {name: repo.get_planet_by_name(name) for name in repo.get_planet_names()},
            "metadata": repo.get_metadata()
        }
        
        repo.save_custom_data(initial_data, backup=True)
        
        # データを変更
        repo.add_planet({
            "name": "一時惑星",
            "mass": 1.0e24,
            "radius": 5000.0,
            "orbital_elements": {
                "semi_major_axis": 2.0,
                "eccentricity": 0.1,
                "inclination": 1.0,
                "longitude_of_ascending_node": 0.0,
                "argument_of_perihelion": 0.0,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 2451545.0
            }
        })
        
        # バックアップファイルの存在確認
        backup_path = self.data_path.with_suffix('.bak')
        assert backup_path.exists()
        
        # バックアップファイルからの復旧シミュレーション
        backup_path.replace(self.data_path)
        
        # 復旧後の確認
        repo_restored = PlanetRepository(self.data_path)
        assert repo_restored.get_planet_by_name("一時惑星") is None
    
    def test_large_dataset_handling(self):
        """大量データの処理テスト"""
        repo = PlanetRepository(self.data_path)
        
        # 100個の仮想惑星を追加
        for i in range(100):
            planet_data = {
                "name": f"惑星{i:03d}",
                "mass": 1.0e24 + i * 1e22,
                "radius": 5000.0 + i * 100,
                "color": [0.5, 0.5, 0.5],
                "rotation_period": 24.0 + i * 0.1,
                "axial_tilt": i * 0.5,
                "orbital_elements": {
                    "semi_major_axis": 1.0 + i * 0.1,
                    "eccentricity": 0.01 + i * 0.001,
                    "inclination": i * 0.1,
                    "longitude_of_ascending_node": i * 3.6,
                    "argument_of_perihelion": i * 1.8,
                    "mean_anomaly_at_epoch": i * 7.2,
                    "epoch": 2451545.0
                }
            }
            
            success = repo.add_planet(planet_data)
            assert success is True
        
        # パフォーマンス測定
        import time
        
        start_time = time.time()
        planet_names = repo.get_planet_names()
        end_time = time.time()
        
        # 大量データでも高速に動作することを確認
        assert len(planet_names) >= 100
        assert end_time - start_time < 1.0  # 1秒以内
        
        # ファイルサイズの確認（合理的な範囲内）
        file_size = self.data_path.stat().st_size
        assert file_size < 10 * 1024 * 1024  # 10MB以内
    
    def test_concurrent_access_simulation(self):
        """同時アクセスのシミュレーションテスト"""
        # 複数のリポジトリインスタンスを作成
        repo1 = PlanetRepository(self.data_path)
        repo2 = PlanetRepository(self.data_path)
        
        # repo1で惑星追加
        planet1 = {
            "name": "同時アクセス惑星1",
            "mass": 1.0e24,
            "radius": 5000.0,
            "orbital_elements": {
                "semi_major_axis": 2.0,
                "eccentricity": 0.1,
                "inclination": 1.0,
                "longitude_of_ascending_node": 0.0,
                "argument_of_perihelion": 0.0,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 2451545.0
            }
        }
        
        success1 = repo1.add_planet(planet1)
        assert success1 is True
        
        # repo2で別の惑星追加（ファイルが更新されていることを確認）
        repo2._load_data()  # 手動でリロード
        
        planet2 = {
            "name": "同時アクセス惑星2",
            "mass": 2.0e24,
            "radius": 6000.0,
            "orbital_elements": {
                "semi_major_axis": 3.0,
                "eccentricity": 0.2,
                "inclination": 2.0,
                "longitude_of_ascending_node": 45.0,
                "argument_of_perihelion": 90.0,
                "mean_anomaly_at_epoch": 180.0,
                "epoch": 2451545.0
            }
        }
        
        success2 = repo2.add_planet(planet2)
        assert success2 is True
        
        # 新しいインスタンスで両方の惑星が確認できることをテスト
        repo3 = PlanetRepository(self.data_path)
        assert repo3.get_planet_by_name("同時アクセス惑星1") is not None
        assert repo3.get_planet_by_name("同時アクセス惑星2") is not None