"""
物理エンジンのテスト
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
        earth.position = np.array([149597870700.0, 0.0, 0.0])  # 1AU (m)
        earth.velocity = np.array([0.0, 29780.0, 0.0])  # 地球の公転速度 (m/s)
        return earth
    
    @pytest.fixture
    def sun_mock(self):
        """太陽のモックオブジェクト"""
        sun = MockCelestialBody("Sun", 1.989e30, 695700000.0)
        sun.position = np.array([0.0, 0.0, 0.0])
        sun.velocity = np.array([0.0, 0.0, 0.0])
        return sun
    
    @pytest.fixture
    def moon_mock(self):
        """月のモックオブジェクト"""
        moon = MockCelestialBody("Moon", 7.342e22, 1737400.0)
        moon.position = np.array([149597870700.0 + 384400000.0, 0.0, 0.0])  # 地球から38万km
        moon.velocity = np.array([0.0, 29780.0 + 1022.0, 0.0])  # 地球の速度 + 月の公転速度
        return moon
    
    def test_physics_engine_initialization(self, physics_engine, math_constants):
        """物理エンジンの初期化テスト"""
        assert physics_engine.gravitational_constant == math_constants["G"]
        assert physics_engine.au_to_km == math_constants["AU"]
    
    def test_gravitational_force_calculation(self, physics_engine, earth_mock, sun_mock, math_constants):
        """重力計算の基本テスト"""
        force = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        
        # 力の大きさを計算
        distance = np.linalg.norm(earth_mock.position - sun_mock.position)
        expected_magnitude = (
            math_constants["G"] * earth_mock.mass * sun_mock.mass / (distance ** 2)
        )
        
        force_magnitude = np.linalg.norm(force)
        
        # 1%の誤差を許容
        relative_error = abs(force_magnitude - expected_magnitude) / expected_magnitude
        assert relative_error < 0.01
        
        # 力の方向が太陽向きであることを確認
        direction = force / force_magnitude
        expected_direction = (sun_mock.position - earth_mock.position) / distance
        assert np.allclose(direction, expected_direction, atol=1e-10)
    
    def test_gravitational_force_symmetry(self, physics_engine, earth_mock, sun_mock):
        """重力の相互作用（ニュートンの第3法則）テスト"""
        force_earth_from_sun = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        force_sun_from_earth = physics_engine.calculate_gravitational_force(sun_mock, earth_mock)
        
        # 力の大きさが等しい
        assert np.allclose(
            np.linalg.norm(force_earth_from_sun),
            np.linalg.norm(force_sun_from_earth),
            rtol=1e-12
        )
        
        # 力の方向が反対
        assert np.allclose(
            force_earth_from_sun,
            -force_sun_from_earth,
            rtol=1e-12
        )
    
    def test_gravitational_force_zero_distance(self, physics_engine, earth_mock, sun_mock):
        """ゼロ距離での重力計算エラーテスト"""
        # 同じ位置に配置
        earth_mock.position = sun_mock.position.copy()
        
        with pytest.raises(ValueError, match="距離がゼロ"):
            physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
    
    @pytest.mark.parametrize("distance_multiplier,expected_force_ratio", [
        (2.0, 0.25),    # 距離2倍 → 力1/4
        (3.0, 1/9),     # 距離3倍 → 力1/9
        (0.5, 4.0),     # 距離1/2 → 力4倍
        (10.0, 0.01),   # 距離10倍 → 力1/100
    ])
    def test_inverse_square_law(self, physics_engine, earth_mock, sun_mock, 
                               distance_multiplier, expected_force_ratio):
        """逆二乗法則のテスト"""
        # 基準距離での力
        baseline_force = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        baseline_magnitude = np.linalg.norm(baseline_force)
        
        # 距離を変更
        earth_mock.position *= distance_multiplier
        
        # 変更後の力
        modified_force = physics_engine.calculate_gravitational_force(earth_mock, sun_mock)
        modified_magnitude = np.linalg.norm(modified_force)
        
        # 力の比率確認
        actual_ratio = modified_magnitude / baseline_magnitude
        assert abs(actual_ratio - expected_force_ratio) < 1e-10
    
    def test_solve_kepler_equation_circular_orbit(self, physics_engine):
        """円軌道でのケプラー方程式解法テスト"""
        mean_anomaly = np.pi / 2  # 90度
        eccentricity = 0.0  # 円軌道
        
        eccentric_anomaly = physics_engine.solve_kepler_equation(mean_anomaly, eccentricity)
        
        # 円軌道では離心近点角 = 平均近点角
        assert abs(eccentric_anomaly - mean_anomaly) < 1e-12
    
    @pytest.mark.parametrize("mean_anomaly_deg,eccentricity", [
        (0, 0.1),      # 近日点付近
        (90, 0.3),     # 1/4周
        (180, 0.5),    # 遠日点
        (270, 0.7),    # 3/4周
        (360, 0.9),    # 1周（高離心率）
    ])
    def test_solve_kepler_equation_convergence(self, physics_engine, mean_anomaly_deg, eccentricity):
        """ケプラー方程式の収束性テスト"""
        mean_anomaly = np.radians(mean_anomaly_deg)
        
        eccentric_anomaly = physics_engine.solve_kepler_equation(mean_anomaly, eccentricity)
        
        # ケプラー方程式の検証: M = E - e*sin(E)
        calculated_mean_anomaly = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly)
        
        # 正規化（0-2π）
        calculated_mean_anomaly = calculated_mean_anomaly % (2 * np.pi)
        mean_anomaly = mean_anomaly % (2 * np.pi)
        
        assert abs(calculated_mean_anomaly - mean_anomaly) < 1e-10
    
    def test_solve_kepler_equation_high_eccentricity(self, physics_engine):
        """高離心率でのケプラー方程式解法テスト"""
        mean_anomaly = np.pi  # 180度
        eccentricity = 0.99   # 非常に高い離心率
        
        eccentric_anomaly = physics_engine.solve_kepler_equation(mean_anomaly, eccentricity)
        
        # 解が妥当な範囲内であることを確認
        assert 0 <= eccentric_anomaly <= 2 * np.pi
        
        # ケプラー方程式の検証
        calculated_mean_anomaly = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly)
        assert abs(calculated_mean_anomaly - mean_anomaly) < 1e-8  # 高離心率では精度が少し落ちる
    
    def test_solve_kepler_equation_invalid_eccentricity(self, physics_engine):
        """不正な離心率でのエラーテスト"""
        mean_anomaly = np.pi / 2
        
        # 離心率が1以上（双曲線軌道）
        with pytest.raises(ValueError, match="離心率"):
            physics_engine.solve_kepler_equation(mean_anomaly, 1.0)
        
        with pytest.raises(ValueError, match="離心率"):
            physics_engine.solve_kepler_equation(mean_anomaly, 1.5)
        
        # 負の離心率
        with pytest.raises(ValueError, match="離心率"):
            physics_engine.solve_kepler_equation(mean_anomaly, -0.1)
    
    def test_integrate_motion_energy_conservation(self, physics_engine, earth_mock, sun_mock):
        """運動積分でのエネルギー保存テスト"""
        bodies = [earth_mock, sun_mock]
        dt = 86400.0  # 1日 (秒)
        
        # 初期エネルギー計算
        initial_kinetic = sum(body.get_kinetic_energy() for body in bodies)
        initial_potential = 0.0
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                r = np.linalg.norm(body1.position - body2.position)
                initial_potential -= (physics_engine.gravitational_constant * 
                                    body1.mass * body2.mass / r)
        initial_total = initial_kinetic + initial_potential
        
        # 運動積分を実行（短期間）
        for _ in range(10):  # 10日間
            physics_engine.integrate_motion(bodies, dt)
        
        # 最終エネルギー計算
        final_kinetic = sum(body.get_kinetic_energy() for body in bodies)
        final_potential = 0.0
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                r = np.linalg.norm(body1.position - body2.position)
                final_potential -= (physics_engine.gravitational_constant * 
                                  body1.mass * body2.mass / r)
        final_total = final_kinetic + final_potential
        
        # エネルギー保存（1%の誤差を許容）
        energy_change = abs(final_total - initial_total) / abs(initial_total)
        assert energy_change < 0.01
    
    def test_integrate_motion_momentum_conservation(self, physics_engine, earth_mock, sun_mock):
        """運動積分での運動量保存テスト"""
        bodies = [earth_mock, sun_mock]
        dt = 86400.0  # 1日 (秒)
        
        # 初期運動量計算
        initial_momentum = sum(body.get_momentum() for body in bodies)
        
        # 運動積分を実行
        for _ in range(5):  # 5日間
            physics_engine.integrate_motion(bodies, dt)
        
        # 最終運動量計算
        final_momentum = sum(body.get_momentum() for body in bodies)
        
        # 運動量保存（外力がないため）
        momentum_change = np.linalg.norm(final_momentum - initial_momentum)
        total_momentum = np.linalg.norm(initial_momentum)
        
        # 相対的な変化が0.1%以下
        if total_momentum > 0:
            relative_change = momentum_change / total_momentum
            assert relative_change < 0.001
        else:
            assert momentum_change < 1e10  # 絶対値での許容範囲
    
    def test_three_body_problem(self, physics_engine, earth_mock, sun_mock, moon_mock):
        """3体問題のテスト"""
        bodies = [earth_mock, sun_mock, moon_mock]
        dt = 3600.0  # 1時間 (秒)
        
        # 初期状態を記録
        initial_positions = [body.position.copy() for body in bodies]
        
        # 短期間の積分
        for _ in range(24):  # 1日間
            physics_engine.integrate_motion(bodies, dt)
        
        # 全ての天体が移動していることを確認
        for i, body in enumerate(bodies):
            position_change = np.linalg.norm(body.position - initial_positions[i])
            assert position_change > 1000.0  # 1km以上移動
    
    def test_runge_kutta_accuracy(self, physics_engine):
        """ルンゲ・クッタ法の精度テスト"""
        # 解析的に解ける簡単な問題でテスト
        # dx/dt = -x, x(0) = 1 の解は x(t) = exp(-t)
        
        # モック関数を使用して微分方程式を設定
        def simple_ode(t, x):
            return -x
        
        # 数値積分の結果と解析解を比較
        t0, x0 = 0.0, 1.0
        dt = 0.1
        steps = 10
        
        # 数値解
        t, x = t0, x0
        for _ in range(steps):
            k1 = dt * simple_ode(t, x)
            k2 = dt * simple_ode(t + dt/2, x + k1/2)
            k3 = dt * simple_ode(t + dt/2, x + k2/2)
            k4 = dt * simple_ode(t + dt, x + k3)
            x += (k1 + 2*k2 + 2*k3 + k4) / 6
            t += dt
        
        # 解析解
        analytical_solution = np.exp(-t)
        
        # 4次ルンゲ・クッタ法の精度確認
        error = abs(x - analytical_solution)
        assert error < 1e-6  # 高精度であることを確認
    
    def test_calculate_orbital_velocity(self, physics_engine, math_constants):
        """軌道速度計算のテスト"""
        # 地球軌道での円軌道速度
        orbital_radius = math_constants["AU"] * 1000  # m
        central_mass = math_constants["SOLAR_MASS"]
        
        orbital_velocity = physics_engine.calculate_orbital_velocity(orbital_radius, central_mass)
        
        # 理論値: v = sqrt(GM/r)
        expected_velocity = np.sqrt(math_constants["G"] * central_mass / orbital_radius)
        
        relative_error = abs(orbital_velocity - expected_velocity) / expected_velocity
        assert relative_error < 1e-12
    
    def test_escape_velocity(self, physics_engine, math_constants):
        """脱出速度計算のテスト"""
        # 地球表面からの脱出速度
        earth_radius = 6371000.0  # m
        earth_mass = math_constants["EARTH_MASS"]
        
        escape_velocity = physics_engine.calculate_escape_velocity(earth_radius, earth_mass)
        
        # 理論値: v = sqrt(2GM/r)
        expected_velocity = np.sqrt(2 * math_constants["G"] * earth_mass / earth_radius)
        
        relative_error = abs(escape_velocity - expected_velocity) / expected_velocity
        assert relative_error < 1e-12