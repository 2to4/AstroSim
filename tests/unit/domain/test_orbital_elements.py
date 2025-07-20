"""
軌道要素クラスのテスト
"""

import pytest
import numpy as np
from src.domain.orbital_elements import OrbitalElements


class TestOrbitalElements:
    """軌道要素クラスのテスト"""
    
    def test_orbital_elements_initialization(self, sample_orbital_elements):
        """軌道要素の初期化テスト"""
        elements = OrbitalElements(**sample_orbital_elements)
        
        assert elements.semi_major_axis == sample_orbital_elements["semi_major_axis"]
        assert elements.eccentricity == sample_orbital_elements["eccentricity"]
        assert elements.inclination == sample_orbital_elements["inclination"]
        
        # 角度は0-360度に正規化されるため、正規化後の値と比較
        expected_lon_asc_node = sample_orbital_elements["longitude_of_ascending_node"] % 360.0
        expected_arg_perihelion = sample_orbital_elements["argument_of_perihelion"] % 360.0
        expected_mean_anomaly = sample_orbital_elements["mean_anomaly_at_epoch"] % 360.0
        
        assert elements.longitude_of_ascending_node == expected_lon_asc_node
        assert elements.argument_of_perihelion == expected_arg_perihelion
        assert elements.mean_anomaly_at_epoch == expected_mean_anomaly
        assert elements.epoch == sample_orbital_elements["epoch"]
    
    @pytest.mark.parametrize("eccentricity,expected_valid", [
        (0.0, True),      # 円軌道
        (0.5, True),      # 楕円軌道
        (0.9, True),      # 細長い楕円軌道
        (1.0, False),     # 放物線軌道（境界値）
        (1.1, False),     # 双曲線軌道
        (-0.1, False),    # 負の離心率
    ])
    def test_eccentricity_validation(self, sample_orbital_elements, eccentricity, expected_valid):
        """離心率の妥当性検証"""
        sample_orbital_elements["eccentricity"] = eccentricity
        
        if expected_valid:
            elements = OrbitalElements(**sample_orbital_elements)
            assert elements.eccentricity == eccentricity
        else:
            with pytest.raises(ValueError, match="離心率"):
                OrbitalElements(**sample_orbital_elements)
    
    @pytest.mark.parametrize("semi_major_axis,expected_valid", [
        (0.1, True),      # 水星より近い
        (1.0, True),      # 地球軌道
        (30.0, True),     # 海王星軌道
        (100.0, True),    # 外縁天体
        (0.0, False),     # ゼロ
        (-1.0, False),    # 負値
    ])
    def test_semi_major_axis_validation(self, sample_orbital_elements, semi_major_axis, expected_valid):
        """軌道長半径の妥当性検証"""
        sample_orbital_elements["semi_major_axis"] = semi_major_axis
        
        if expected_valid:
            elements = OrbitalElements(**sample_orbital_elements)
            assert elements.semi_major_axis == semi_major_axis
        else:
            with pytest.raises(ValueError, match="軌道長半径"):
                OrbitalElements(**sample_orbital_elements)
    
    def test_angle_normalization(self, sample_orbital_elements):
        """角度の正規化テスト"""
        # 360度を超える角度
        sample_orbital_elements["mean_anomaly_at_epoch"] = 450.0
        elements = OrbitalElements(**sample_orbital_elements)
        assert 0 <= elements.mean_anomaly_at_epoch < 360
        
        # 負の角度
        sample_orbital_elements["inclination"] = -30.0
        elements = OrbitalElements(**sample_orbital_elements)
        assert 0 <= elements.inclination < 360
    
    def test_orbital_period_calculation(self, earth_data, math_constants):
        """軌道周期の計算テスト（地球）"""
        elements = OrbitalElements(**earth_data["orbital_elements"])
        
        calculated_period = elements.get_orbital_period()
        
        # 地球の軌道周期は約365.25日（1年）
        expected_period = 365.25
        
        # 1%の誤差を許容
        assert abs(calculated_period - expected_period) / expected_period < 0.01
    
    def test_perihelion_aphelion_distances(self, earth_data):
        """近日点・遠日点距離の計算テスト"""
        elements = OrbitalElements(**earth_data["orbital_elements"])
        
        perihelion = elements.get_perihelion_distance()
        aphelion = elements.get_aphelion_distance()
        
        # 物理的に正しい関係
        assert perihelion < aphelion
        assert perihelion == elements.semi_major_axis * (1 - elements.eccentricity)
        assert aphelion == elements.semi_major_axis * (1 + elements.eccentricity)
    
    @pytest.mark.parametrize("planet_name,expected_period", [
        ("水星", 87.969),
        ("金星", 224.701),
        ("地球", 365.256),
        ("火星", 687.0),
    ])
    def test_known_orbital_periods(self, planet_name, expected_period):
        """既知の惑星軌道周期との比較"""
        # 実際の惑星データを使用してテストする予定
        # 現在はプレースホルダー
        pass
    
    def test_copy_and_equality(self, sample_orbital_elements):
        """軌道要素のコピーと等価性テスト"""
        elements1 = OrbitalElements(**sample_orbital_elements)
        elements2 = OrbitalElements(**sample_orbital_elements)
        
        # 等価性
        assert elements1 == elements2
        
        # コピー
        elements3 = elements1.copy()
        assert elements3 == elements1
        assert elements3 is not elements1
    
    def test_to_dict(self, sample_orbital_elements):
        """辞書変換テスト"""
        elements = OrbitalElements(**sample_orbital_elements)
        result_dict = elements.to_dict()
        
        # 角度以外の要素は元の値と一致
        assert result_dict["semi_major_axis"] == sample_orbital_elements["semi_major_axis"]
        assert result_dict["eccentricity"] == sample_orbital_elements["eccentricity"]
        assert result_dict["epoch"] == sample_orbital_elements["epoch"]
        
        # 角度は正規化後の値と一致
        assert result_dict["inclination"] == sample_orbital_elements["inclination"] % 360.0
        assert result_dict["longitude_of_ascending_node"] == sample_orbital_elements["longitude_of_ascending_node"] % 360.0
        assert result_dict["argument_of_perihelion"] == sample_orbital_elements["argument_of_perihelion"] % 360.0
        assert result_dict["mean_anomaly_at_epoch"] == sample_orbital_elements["mean_anomaly_at_epoch"] % 360.0
    
    def test_from_dict(self, sample_orbital_elements):
        """辞書からの作成テスト"""
        elements = OrbitalElements.from_dict(sample_orbital_elements)
        
        assert elements.semi_major_axis == sample_orbital_elements["semi_major_axis"]
        assert elements.eccentricity == sample_orbital_elements["eccentricity"]