"""
物理エンジンのテスト（実装に合わせた簡略版）
"""

import pytest
import numpy as np
from src.simulation.physics_engine import PhysicsEngine
from src.domain.celestial_body import CelestialBody


class MockCelestialBody(CelestialBody):
    """テスト用モック天体クラス"""
    
    def update_position(self, julian_date: float) -> None:
        pass
    
    def get_visual_properties(self) -> dict:
        return {}


class TestPhysicsEngine:
    """物理エンジンのテスト"""
    
    @pytest.fixture
    def physics_engine(self):
        """物理エンジンのフィクスチャ"""
        return PhysicsEngine()
    
    @pytest.fixture
    def earth_mock(self):
        """地球のモックオブジェクト"""
        earth = MockCelestialBody("Earth", 5.972e24, 6371.0)
        earth.position = np.array([149597870.7, 0.0, 0.0])  # 1AU (km)
        earth.velocity = np.array([0.0, 29.78, 0.0])  # 地球の公転速度 (km/s)
        return earth
    
    @pytest.fixture
    def sun_mock(self):
        """太陽のモックオブジェクト"""
        sun = MockCelestialBody("Sun", 1.989e30, 695700.0)
        sun.position = np.array([0.0, 0.0, 0.0])  # km
        sun.velocity = np.array([0.0, 0.0, 0.0])  # km/s
        return sun
    
    def test_physics_engine_initialization(self, physics_engine):
        """物理エンジンの初期化テスト"""
        assert physics_engine.gravitational_constant == 6.67430e-11
        assert physics_engine.au_to_km == 149597870.7
        assert physics_engine.integration_method == "rk4"
        assert physics_engine.convergence_tolerance == 1e-12
        assert physics_engine.max_iterations == 20
    
    def test_gravitational_force_calculation(self, physics_engine, earth_mock, sun_mock):
        """重力加速度計算の基本テスト"""
        acceleration = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        
        # 結果の形式を確認
        assert isinstance(acceleration, np.ndarray)
        assert len(acceleration) == 3
        
        # 距離を計算（m単位に変換）
        distance = np.linalg.norm((earth_mock.position - sun_mock.position) * 1000)  # km -> m
        
        # 期待される加速度: a = GM/r² (earth_mockに対する)
        expected_magnitude = physics_engine.gravitational_constant * sun_mock.mass / (distance ** 2)
        
        acceleration_magnitude = np.linalg.norm(acceleration)
        
        # 1%の誤差を許容
        relative_error = abs(acceleration_magnitude - expected_magnitude) / expected_magnitude
        assert relative_error < 0.01
        
        # 加速度の方向が太陽向きであることを確認
        direction = acceleration / acceleration_magnitude
        expected_direction = (sun_mock.position - earth_mock.position) / np.linalg.norm(sun_mock.position - earth_mock.position)
        assert np.allclose(direction, expected_direction, atol=1e-10)
    
    def test_gravitational_force_zero_distance(self, physics_engine, earth_mock, sun_mock):
        """ゼロ距離での重力計算エラーテスト"""
        # 同じ位置に配置
        earth_mock.position = sun_mock.position.copy()
        
        with pytest.raises(ValueError, match="距離がゼロ"):
            physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
    
    def test_solve_kepler_equation_circular_orbit(self, physics_engine):
        """円軌道でのケプラー方程式解法テスト"""
        mean_anomaly = np.pi / 2  # 90度
        eccentricity = 0.0  # 円軌道
        
        eccentric_anomaly = physics_engine.solve_kepler_equation(mean_anomaly, eccentricity)
        
        # 円軌道では離心近点角 = 平均近点角
        assert abs(eccentric_anomaly - mean_anomaly) < 1e-12
    
    def test_solve_kepler_equation_convergence(self, physics_engine):
        """ケプラー方程式の収束性テスト"""
        mean_anomaly = np.radians(90)  # 90度
        eccentricity = 0.3
        
        eccentric_anomaly = physics_engine.solve_kepler_equation(mean_anomaly, eccentricity)
        
        # ケプラー方程式の検証: M = E - e*sin(E)
        calculated_mean_anomaly = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly)
        
        assert abs(calculated_mean_anomaly - mean_anomaly) < 1e-10
    
    def test_solve_kepler_equation_invalid_eccentricity(self, physics_engine):
        """不正な離心率でのエラーテスト"""
        mean_anomaly = np.pi / 2
        
        # 離心率が1以上（双曲線軌道）
        with pytest.raises(ValueError, match="離心率"):
            physics_engine.solve_kepler_equation(mean_anomaly, 1.0)
        
        # 負の離心率
        with pytest.raises(ValueError, match="離心率"):
            physics_engine.solve_kepler_equation(mean_anomaly, -0.1)
    
    def test_calculate_orbital_velocity(self, physics_engine):
        """軌道速度計算のテスト"""
        # 地球軌道での円軌道速度
        position = np.array([149597870.7, 0.0, 0.0])  # km
        central_mass = 1.989e30  # 太陽質量
        
        orbital_velocity = physics_engine.calculate_orbital_velocity(position, central_mass)
        
        # 理論値: v = sqrt(GM/r)
        r_m = 149597870.7 * 1000  # km -> m
        expected_velocity = np.sqrt(physics_engine.gravitational_constant * central_mass / r_m) / 1000  # km/s
        
        relative_error = abs(orbital_velocity - expected_velocity) / expected_velocity
        assert relative_error < 1e-12
    
    def test_calculate_escape_velocity(self, physics_engine):
        """脱出速度計算のテスト"""
        # 地球表面からの脱出速度
        position = np.array([6371.0, 0.0, 0.0])  # km
        earth_mass = 5.972e24
        
        escape_velocity = physics_engine.calculate_escape_velocity(position, earth_mass)
        
        # 理論値: v = sqrt(2GM/r)
        r_m = 6371000.0  # m
        expected_velocity = np.sqrt(2 * physics_engine.gravitational_constant * earth_mass / r_m) / 1000  # km/s
        
        relative_error = abs(escape_velocity - expected_velocity) / expected_velocity
        assert relative_error < 1e-12
    
    def test_total_force_calculation(self, physics_engine, earth_mock, sun_mock):
        """合計重力計算のテスト"""
        other_bodies = [sun_mock]
        
        total_force = physics_engine.calculate_total_force(earth_mock, other_bodies)
        
        # 単一の力と等しいはず
        single_force = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        
        assert np.allclose(total_force, single_force)
    
    def test_rk4_integration_basic(self, physics_engine, earth_mock, sun_mock):
        """RK4積分の基本テスト"""
        bodies = [earth_mock, sun_mock]
        dt = 86400.0  # 1日 (秒)
        
        # 初期位置を記録
        initial_position = earth_mock.position.copy()
        
        # 1ステップの積分
        physics_engine.integrate_motion_rk4(bodies, dt)
        
        # 位置が変化していることを確認
        position_change = np.linalg.norm(earth_mock.position - initial_position)
        assert position_change > 1.0  # 1km以上移動
    
    def test_set_integration_method(self, physics_engine):
        """積分法設定のテスト"""
        # 有効な積分法
        physics_engine.set_integration_method("rk4")
        assert physics_engine.integration_method == "rk4"
        
        physics_engine.set_integration_method("euler")
        assert physics_engine.integration_method == "euler"
        
        # 無効な積分法
        with pytest.raises(ValueError, match="無効な積分法"):
            physics_engine.set_integration_method("invalid")
    
    def test_string_representation(self, physics_engine):
        """文字列表現のテスト"""
        str_repr = str(physics_engine)
        assert "PhysicsEngine" in str_repr
        assert "rk4" in str_repr
        assert "1e-12" in str_repr