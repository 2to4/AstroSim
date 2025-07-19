"""
テスト共通設定とフィクスチャ定義
"""

import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json
import tempfile

# テストデータのベースパス
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_data_dir():
    """テストデータディレクトリのパス"""
    return TEST_DATA_DIR


@pytest.fixture
def sample_orbital_elements():
    """サンプル軌道要素データ"""
    return {
        "semi_major_axis": 1.00000261,      # AU
        "eccentricity": 0.01671123,
        "inclination": 0.00001531,          # 度
        "longitude_of_ascending_node": -11.26064,  # 度
        "argument_of_perihelion": 114.20783,       # 度
        "mean_anomaly_at_epoch": 358.617,          # 度
        "epoch": 2451545.0                         # J2000.0
    }


@pytest.fixture
def sample_planet_data():
    """サンプル惑星データ"""
    return {
        "name": "TestPlanet",
        "name_en": "TestPlanet",
        "mass": 5.972e24,        # kg
        "radius": 6371.0,        # km
        "color": [0.0, 0.5, 1.0],
        "orbital_elements": {
            "semi_major_axis": 1.0,
            "eccentricity": 0.0167,
            "inclination": 0.0,
            "longitude_of_ascending_node": 0.0,
            "argument_of_perihelion": 0.0,
            "mean_anomaly_at_epoch": 0.0,
            "epoch": 2451545.0
        },
        "physical_properties": {
            "rotation_period": 23.934,  # 時間
            "axial_tilt": 23.44        # 度
        }
    }


@pytest.fixture
def earth_data():
    """地球の実際のデータ"""
    return {
        "name": "地球",
        "name_en": "Earth",
        "mass": 5.972e24,
        "radius": 6371.0,
        "color": [0.0, 0.5, 1.0],
        "orbital_elements": {
            "semi_major_axis": 1.00000261,
            "eccentricity": 0.01671123,
            "inclination": 0.00001531,
            "longitude_of_ascending_node": -11.26064,
            "argument_of_perihelion": 114.20783,
            "mean_anomaly_at_epoch": 358.617,
            "epoch": 2451545.0
        },
        "physical_properties": {
            "rotation_period": 23.934,
            "axial_tilt": 23.44
        }
    }


@pytest.fixture
def mars_data():
    """火星の実際のデータ"""
    return {
        "name": "火星",
        "name_en": "Mars",
        "mass": 6.39e23,
        "radius": 3389.5,
        "color": [1.0, 0.5, 0.0],
        "orbital_elements": {
            "semi_major_axis": 1.52371034,
            "eccentricity": 0.09339410,
            "inclination": 1.84969142,
            "longitude_of_ascending_node": -4.55343205,
            "argument_of_perihelion": -23.94362959,
            "mean_anomaly_at_epoch": 19.39645915,
            "epoch": 2451545.0
        },
        "physical_properties": {
            "rotation_period": 24.623,
            "axial_tilt": 25.19
        }
    }


@pytest.fixture
def test_solar_system_data():
    """テスト用太陽系データ"""
    return {
        "sun": {
            "name": "太陽",
            "name_en": "Sun",
            "mass": 1.989e30,
            "radius": 695700.0,
            "color": [1.0, 1.0, 0.0]
        },
        "planets": [
            {
                "name": "水星",
                "name_en": "Mercury",
                "mass": 3.3011e23,
                "radius": 2439.7,
                "color": [0.8, 0.7, 0.6],
                "orbital_elements": {
                    "semi_major_axis": 0.38709927,
                    "eccentricity": 0.20563593,
                    "inclination": 7.00497902,
                    "longitude_of_ascending_node": 48.33076593,
                    "argument_of_perihelion": 77.45779628,
                    "mean_anomaly_at_epoch": 252.25032350,
                    "epoch": 2451545.0
                }
            },
            {
                "name": "金星",
                "name_en": "Venus",
                "mass": 4.8675e24,
                "radius": 6051.8,
                "color": [1.0, 0.8, 0.0],
                "orbital_elements": {
                    "semi_major_axis": 0.72333566,
                    "eccentricity": 0.00677672,
                    "inclination": 3.39467605,
                    "longitude_of_ascending_node": 76.67984255,
                    "argument_of_perihelion": 131.60246718,
                    "mean_anomaly_at_epoch": 181.97909950,
                    "epoch": 2451545.0
                }
            }
        ]
    }


@pytest.fixture
def j2000_epoch():
    """J2000.0 元期のユリウス日"""
    return 2451545.0


@pytest.fixture
def test_dates():
    """テスト用の日付リスト"""
    return {
        "j2000": 2451545.0,
        "y2024_jan_1": 2460310.5,
        "y2025_jan_1": 2460676.5,
        "future_date": 2470000.0
    }


@pytest.fixture
def temp_config_file():
    """一時的な設定ファイル"""
    config_data = {
        "application": {
            "window_size": [1920, 1080],
            "fullscreen": False,
            "language": "ja"
        },
        "simulation": {
            "start_date": "2024-01-01T00:00:00",
            "time_scale": 1.0,
            "show_orbits": True,
            "show_labels": True
        },
        "graphics": {
            "antialiasing": 4,
            "texture_quality": "high"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        temp_file_path = f.name
    
    yield Path(temp_file_path)
    
    # クリーンアップ
    Path(temp_file_path).unlink()


@pytest.fixture
def temp_planet_data_file():
    """一時的な惑星データファイル"""
    planet_data = {
        "planets": [
            {
                "name": "地球",
                "name_en": "Earth",
                "mass": 5.972e24,
                "radius": 6371.0,
                "color": [0.0, 0.5, 1.0],
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
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(planet_data, f, indent=2, ensure_ascii=False)
        temp_file_path = f.name
    
    yield Path(temp_file_path)
    
    # クリーンアップ
    Path(temp_file_path).unlink()


# カスタムマッチャー
class ApproximatelyEqual:
    """浮動小数点数の近似比較用クラス"""
    
    def __init__(self, expected, tolerance=1e-10):
        self.expected = expected
        self.tolerance = tolerance
    
    def __eq__(self, actual):
        if isinstance(self.expected, (list, tuple, np.ndarray)):
            return np.allclose(actual, self.expected, atol=self.tolerance)
        return abs(actual - self.expected) <= self.tolerance
    
    def __repr__(self):
        return f"approximately {self.expected} (±{self.tolerance})"


@pytest.fixture
def approx():
    """近似比較のためのヘルパー"""
    return ApproximatelyEqual


# テスト用の数学的定数
@pytest.fixture
def math_constants():
    """数学的定数"""
    return {
        "AU": 149597870.7,          # 天文単位 (km)
        "G": 6.67430e-11,           # 重力定数 (m^3 kg^-1 s^-2)
        "SOLAR_MASS": 1.989e30,     # 太陽質量 (kg)
        "EARTH_MASS": 5.972e24,     # 地球質量 (kg)
        "SIDEREAL_YEAR": 365.25636, # 恒星年 (日)
        "PI": np.pi
    }


# テスト実行前のセットアップ
def pytest_configure(config):
    """pytest設定時の初期化処理"""
    # テストデータディレクトリが存在しない場合は作成
    TEST_DATA_DIR.mkdir(exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """テスト収集時の修正処理"""
    # 遅いテストにマークを追加
    for item in items:
        if "performance" in item.nodeid or "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)


# テスト用のカスタムアサーション
def assert_vector_equal(actual, expected, tolerance=1e-10):
    """ベクトルの等価性をテスト"""
    assert np.allclose(actual, expected, atol=tolerance), \
        f"Vectors not equal: {actual} != {expected} (tolerance: {tolerance})"


def assert_orbital_period_correct(semi_major_axis, calculated_period, tolerance=0.01):
    """軌道周期の正確性をテスト（ケプラーの第3法則）"""
    # P^2 = a^3 (太陽質量を1とする単位系)
    expected_period = np.sqrt(semi_major_axis**3) * 365.25  # 日
    assert abs(calculated_period - expected_period) <= tolerance, \
        f"Orbital period incorrect: {calculated_period} != {expected_period} days"


# グローバルにアサーション関数を利用可能にする
pytest.assert_vector_equal = assert_vector_equal
pytest.assert_orbital_period_correct = assert_orbital_period_correct