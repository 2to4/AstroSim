"""
軌道計算クラスの簡略化されたテスト

実装に合わせて主要機能のみをテストします。
"""

import pytest
import numpy as np
from src.simulation.orbit_calculator import OrbitCalculator
from src.domain.orbital_elements import OrbitalElements


class TestOrbitCalculator:
    """軌道計算クラスのテスト"""
    
    @pytest.fixture
    def orbit_calculator(self):
        """軌道計算機のフィクスチャ"""
        return OrbitCalculator()
    
    @pytest.fixture
    def earth_elements(self):
        """地球の軌道要素"""
        return OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.0167,
            inclination=0.0,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=102.9,
            mean_anomaly_at_epoch=100.5,
            epoch=2451545.0
        )
    
    def test_initialization(self, orbit_calculator):
        """初期化テスト"""
        assert orbit_calculator.gravitational_constant > 0
        assert orbit_calculator.solar_mass > 0
        assert orbit_calculator.au_to_km > 0
        assert orbit_calculator.convergence_tolerance > 0
        assert orbit_calculator.max_iterations > 0
    
    def test_position_velocity_calculation(self, orbit_calculator, earth_elements):
        """位置・速度計算の基本テスト"""
        position, velocity = orbit_calculator.calculate_position_velocity(
            earth_elements, 2451545.0
        )
        
        # 結果の形式を確認
        assert isinstance(position, np.ndarray)
        assert isinstance(velocity, np.ndarray)
        assert len(position) == 3
        assert len(velocity) == 3
        
        # 地球軌道の妥当な値であることを確認
        distance = np.linalg.norm(position)
        speed = np.linalg.norm(velocity)
        
        # 地球の軌道半径は約1AU = 149,597,870.7 km
        assert 1.4e8 < distance < 1.6e8  # km
        
        # 地球の公転速度は約30 km/s
        assert 20 < speed < 40  # km/s
    
    def test_orbital_period_calculation(self, orbit_calculator, earth_elements):
        """軌道周期計算テスト"""
        period = orbit_calculator.calculate_orbital_period(earth_elements)
        
        # 地球の軌道周期は約365.25日
        assert 360 < period < 370
    
    def test_kepler_equation_solver(self, orbit_calculator):
        """ケプラー方程式求解テスト"""
        mean_anomaly = np.pi / 2
        eccentricity = 0.1
        
        eccentric_anomaly = orbit_calculator._solve_kepler_equation(
            mean_anomaly, eccentricity
        )
        
        # ケプラー方程式の検証: M = E - e*sin(E)
        calculated_mean = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly)
        assert abs(calculated_mean - mean_anomaly) < 1e-12
    
    def test_true_anomaly_calculation(self, orbit_calculator):
        """真近点角計算テスト"""
        eccentric_anomaly = np.pi / 3
        eccentricity = 0.1
        
        true_anomaly = orbit_calculator._calculate_true_anomaly(
            eccentric_anomaly, eccentricity
        )
        
        # 結果が妥当な範囲内にあることを確認
        assert 0 <= true_anomaly <= 2 * np.pi
        
        # 楕円軌道では真近点角 ≠ 離心近点角
        assert abs(true_anomaly - eccentric_anomaly) > 1e-10
    
    def test_cache_functionality(self, orbit_calculator, earth_elements):
        """キャッシュ機能のテスト"""
        # 最初の計算
        pos1, vel1 = orbit_calculator.calculate_position_velocity(
            earth_elements, 2451545.0
        )
        
        # 同じ計算を再実行
        pos2, vel2 = orbit_calculator.calculate_position_velocity(
            earth_elements, 2451545.0
        )
        
        # 結果が同じであることを確認
        assert np.allclose(pos1, pos2)
        assert np.allclose(vel1, vel2)
        
        # キャッシュ統計を確認
        stats = orbit_calculator.get_cache_stats()
        assert stats["cache_hit_count"] >= 1
    
    def test_orbital_periodicity(self, orbit_calculator, earth_elements):
        """軌道の周期性テスト"""
        period = orbit_calculator.calculate_orbital_period(earth_elements)
        
        # 初期位置
        pos1, _ = orbit_calculator.calculate_position_velocity(
            earth_elements, 2451545.0
        )
        
        # 1周期後の位置
        pos2, _ = orbit_calculator.calculate_position_velocity(
            earth_elements, 2451545.0 + period
        )
        
        # 位置が近いことを確認（軌道半径の10%以内）
        position_diff = np.linalg.norm(pos2 - pos1)
        orbit_radius = np.linalg.norm(pos1)
        
        assert position_diff / orbit_radius < 0.1