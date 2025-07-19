"""
軌道計算クラスのテスト
"""

import pytest
import numpy as np
from src.simulation.orbit_calculator import OrbitCalculator
from src.domain.orbital_elements import OrbitalElements


class TestOrbitCalculator:
    """軌道計算クラスのテスト"""
    
    @pytest.fixture
    def orbit_calculator(self):
        """軌道計算のフィクスチャ"""
        return OrbitCalculator()
    
    @pytest.fixture
    def earth_orbital_elements(self, earth_data):
        """地球の軌道要素"""
        return OrbitalElements(**earth_data["orbital_elements"])
    
    @pytest.fixture
    def circular_orbital_elements(self):
        """円軌道の軌道要素"""
        return OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.0,
            inclination=0.0,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0,
            epoch=2451545.0
        )
    
    @pytest.fixture
    def elliptical_orbital_elements(self):
        """楕円軌道の軌道要素"""
        return OrbitalElements(
            semi_major_axis=1.5,
            eccentricity=0.3,
            inclination=10.0,
            longitude_of_ascending_node=45.0,
            argument_of_perihelion=90.0,
            mean_anomaly_at_epoch=180.0,
            epoch=2451545.0
        )
    
    def test_orbit_calculator_initialization(self, orbit_calculator, math_constants):
        """軌道計算の初期化テスト"""
        assert orbit_calculator.gravitational_parameter == math_constants["G"] * math_constants["SOLAR_MASS"]
        assert orbit_calculator.au_to_m == math_constants["AU"] * 1000
    
    def test_mean_anomaly_calculation(self, orbit_calculator, earth_orbital_elements, j2000_epoch):
        """平均近点角の計算テスト"""
        # J2000での平均近点角（元期での値）
        mean_anomaly_j2000 = orbit_calculator.calculate_mean_anomaly(
            earth_orbital_elements, j2000_epoch
        )
        
        # 元期での平均近点角と一致するはず
        expected_anomaly = np.radians(earth_orbital_elements.mean_anomaly_at_epoch)
        assert abs(mean_anomaly_j2000 - expected_anomaly) < 1e-10
        
        # 1年後の平均近点角
        one_year_later = j2000_epoch + 365.25
        mean_anomaly_later = orbit_calculator.calculate_mean_anomaly(
            earth_orbital_elements, one_year_later
        )
        
        # ほぼ1周（2π）進んでいるはず
        anomaly_change = mean_anomaly_later - mean_anomaly_j2000
        expected_change = 2 * np.pi
        
        # 正規化して比較
        anomaly_change = anomaly_change % (2 * np.pi)
        assert abs(anomaly_change - 0.0) < 0.1  # 1年で1周なので0に近い
    
    def test_eccentric_anomaly_calculation(self, orbit_calculator, earth_orbital_elements):
        """離心近点角の計算テスト"""
        mean_anomaly = np.pi / 2  # 90度
        
        eccentric_anomaly = orbit_calculator.calculate_eccentric_anomaly(
            mean_anomaly, earth_orbital_elements.eccentricity
        )
        
        # ケプラー方程式の検証: M = E - e*sin(E)
        calculated_mean = eccentric_anomaly - earth_orbital_elements.eccentricity * np.sin(eccentric_anomaly)
        assert abs(calculated_mean - mean_anomaly) < 1e-12
    
    def test_true_anomaly_calculation(self, orbit_calculator, earth_orbital_elements):
        """真近点角の計算テスト"""
        eccentric_anomaly = np.pi / 3  # 60度
        
        true_anomaly = orbit_calculator.calculate_true_anomaly(
            eccentric_anomaly, earth_orbital_elements.eccentricity
        )
        
        # 楕円軌道では真近点角は離心近点角と異なる
        assert true_anomaly != eccentric_anomaly
        
        # 0から2πの範囲内
        assert 0 <= true_anomaly <= 2 * np.pi
    
    def test_true_anomaly_circular_orbit(self, orbit_calculator, circular_orbital_elements):
        """円軌道での真近点角計算テスト"""
        eccentric_anomaly = np.pi / 4  # 45度
        
        true_anomaly = orbit_calculator.calculate_true_anomaly(
            eccentric_anomaly, circular_orbital_elements.eccentricity
        )
        
        # 円軌道では真近点角 = 離心近点角
        assert abs(true_anomaly - eccentric_anomaly) < 1e-12
    
    def test_orbital_position_calculation(self, orbit_calculator, circular_orbital_elements):
        """軌道面での位置計算テスト"""
        true_anomaly = 0.0  # 近日点
        
        position = orbit_calculator.calculate_orbital_position(
            true_anomaly, circular_orbital_elements
        )
        
        # 近日点での位置（軌道面でのx軸正方向）
        expected_distance = circular_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
        expected_position = np.array([expected_distance, 0.0])
        
        assert np.allclose(position, expected_position, rtol=1e-12)
    
    def test_orbital_position_elliptical(self, orbit_calculator, elliptical_orbital_elements):
        """楕円軌道での位置計算テスト"""
        # 近日点と遠日点での位置
        true_anomaly_perihelion = 0.0
        true_anomaly_aphelion = np.pi
        
        pos_perihelion = orbit_calculator.calculate_orbital_position(
            true_anomaly_perihelion, elliptical_orbital_elements
        )
        pos_aphelion = orbit_calculator.calculate_orbital_position(
            true_anomaly_aphelion, elliptical_orbital_elements
        )
        
        # 距離の計算
        r_perihelion = np.linalg.norm(pos_perihelion)
        r_aphelion = np.linalg.norm(pos_aphelion)
        
        # 楕円軌道の性質確認
        assert r_perihelion < r_aphelion
        
        # 理論値との比較
        a = elliptical_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
        e = elliptical_orbital_elements.eccentricity
        
        expected_r_perihelion = a * (1 - e)
        expected_r_aphelion = a * (1 + e)
        
        assert abs(r_perihelion - expected_r_perihelion) / expected_r_perihelion < 1e-12
        assert abs(r_aphelion - expected_r_aphelion) / expected_r_aphelion < 1e-12
    
    def test_coordinate_transformation(self, orbit_calculator, elliptical_orbital_elements):
        """座標変換のテスト"""
        orbital_position = np.array([1.0e11, 5.0e10])  # 軌道面での位置
        
        heliocentric_position = orbit_calculator.transform_to_heliocentric(
            orbital_position, elliptical_orbital_elements
        )
        
        # 3D座標になっている
        assert len(heliocentric_position) == 3
        
        # 距離は保存される
        orbital_distance = np.linalg.norm(orbital_position)
        heliocentric_distance = np.linalg.norm(heliocentric_position)
        assert abs(orbital_distance - heliocentric_distance) < 1e-6
    
    def test_coordinate_transformation_zero_inclination(self, orbit_calculator, circular_orbital_elements):
        """傾斜角ゼロでの座標変換テスト"""
        orbital_position = np.array([1.0e11, 0.0])
        
        heliocentric_position = orbit_calculator.transform_to_heliocentric(
            orbital_position, circular_orbital_elements
        )
        
        # 傾斜角0度なのでz成分は0
        assert abs(heliocentric_position[2]) < 1e-10
        
        # xy平面での位置
        assert abs(heliocentric_position[0] - 1.0e11) < 1e-6
        assert abs(heliocentric_position[1]) < 1e-10
    
    def test_full_position_calculation(self, orbit_calculator, earth_orbital_elements, j2000_epoch):
        """完全な位置計算のテスト"""
        position = orbit_calculator.calculate_position(
            earth_orbital_elements, j2000_epoch
        )
        
        # 3D位置ベクトル
        assert len(position) == 3
        
        # 地球軌道半径程度の距離
        distance = np.linalg.norm(position)
        expected_distance = earth_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
        
        # 離心率による変動を考慮して±20%の範囲
        relative_error = abs(distance - expected_distance) / expected_distance
        assert relative_error < 0.2
    
    def test_velocity_calculation(self, orbit_calculator, circular_orbital_elements, j2000_epoch):
        """速度計算のテスト"""
        velocity = orbit_calculator.calculate_velocity(
            circular_orbital_elements, j2000_epoch
        )
        
        # 3D速度ベクトル
        assert len(velocity) == 3
        
        # 円軌道での軌道速度の理論値
        a = circular_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
        expected_speed = np.sqrt(orbit_calculator.gravitational_parameter / a)
        
        actual_speed = np.linalg.norm(velocity)
        relative_error = abs(actual_speed - expected_speed) / expected_speed
        assert relative_error < 0.01
    
    def test_orbital_period_calculation(self, orbit_calculator, earth_orbital_elements):
        """軌道周期の計算テスト"""
        period = orbit_calculator.calculate_orbital_period(earth_orbital_elements)
        
        # ケプラーの第3法則による期待値
        a = earth_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
        expected_period = 2 * np.pi * np.sqrt(a**3 / orbit_calculator.gravitational_parameter)
        expected_period_days = expected_period / 86400  # 秒から日に変換
        
        # 1年程度
        assert 350 < period < 380  # 日
        
        # 理論値との比較（1%の誤差を許容）
        relative_error = abs(period - expected_period_days) / expected_period_days
        assert relative_error < 0.01
    
    @pytest.mark.parametrize("time_offset_days,expected_cycles", [
        (365.25, 1.0),      # 1年で1周
        (182.625, 0.5),     # 半年で半周
        (91.3125, 0.25),    # 1/4年で1/4周
        (730.5, 2.0),       # 2年で2周
    ])
    def test_orbital_motion_periodicity(self, orbit_calculator, circular_orbital_elements, 
                                       j2000_epoch, time_offset_days, expected_cycles):
        """軌道運動の周期性テスト"""
        # 初期位置
        initial_position = orbit_calculator.calculate_position(
            circular_orbital_elements, j2000_epoch
        )
        
        # 指定時間後の位置
        later_position = orbit_calculator.calculate_position(
            circular_orbital_elements, j2000_epoch + time_offset_days
        )
        
        # 角度変化の計算
        initial_angle = np.arctan2(initial_position[1], initial_position[0])
        later_angle = np.arctan2(later_position[1], later_position[0])
        
        angle_change = later_angle - initial_angle
        if angle_change < 0:
            angle_change += 2 * np.pi
        
        actual_cycles = angle_change / (2 * np.pi)
        
        # 期待される周期数との比較（1%の誤差を許容）
        assert abs(actual_cycles - expected_cycles) < 0.01
    
    def test_energy_conservation(self, orbit_calculator, elliptical_orbital_elements, j2000_epoch):
        """エネルギー保存のテスト"""
        times = [j2000_epoch + i * 10 for i in range(37)]  # 1年分、10日間隔
        energies = []
        
        for time in times:
            position = orbit_calculator.calculate_position(elliptical_orbital_elements, time)
            velocity = orbit_calculator.calculate_velocity(elliptical_orbital_elements, time)
            
            # 運動エネルギー
            kinetic_energy = 0.5 * np.linalg.norm(velocity)**2
            
            # ポテンシャルエネルギー
            r = np.linalg.norm(position)
            potential_energy = -orbit_calculator.gravitational_parameter / r
            
            # 全エネルギー
            total_energy = kinetic_energy + potential_energy
            energies.append(total_energy)
        
        # エネルギーが保存されていることを確認
        energy_variations = [abs(e - energies[0]) / abs(energies[0]) for e in energies]
        max_variation = max(energy_variations)
        
        # 数値誤差を考慮して0.1%以下の変動
        assert max_variation < 0.001
    
    def test_angular_momentum_conservation(self, orbit_calculator, elliptical_orbital_elements, j2000_epoch):
        """角運動量保存のテスト"""
        times = [j2000_epoch + i * 15 for i in range(24)]  # 1年分、15日間隔
        angular_momenta = []
        
        for time in times:
            position = orbit_calculator.calculate_position(elliptical_orbital_elements, time)
            velocity = orbit_calculator.calculate_velocity(elliptical_orbital_elements, time)
            
            # 角運動量ベクトル r × v
            angular_momentum = np.cross(position, velocity)
            angular_momenta.append(angular_momentum)
        
        # 角運動量の大きさが保存されていることを確認
        magnitudes = [np.linalg.norm(L) for L in angular_momenta]
        magnitude_variations = [abs(m - magnitudes[0]) / magnitudes[0] for m in magnitudes]
        max_variation = max(magnitude_variations)
        
        # 0.1%以下の変動
        assert max_variation < 0.001
        
        # 角運動量ベクトルの方向も保存されている
        for L in angular_momenta[1:]:
            dot_product = np.dot(angular_momenta[0], L) / (np.linalg.norm(angular_momenta[0]) * np.linalg.norm(L))
            # cos(角度) が1に近い（角度が小さい）
            assert dot_product > 0.999
    
    def test_vis_viva_equation(self, orbit_calculator, elliptical_orbital_elements, j2000_epoch):
        """ビス・ビバ方程式のテスト"""
        # 複数の時刻で位置と速度を計算
        times = [j2000_epoch + i * 30 for i in range(12)]  # 1年分、30日間隔
        
        for time in times:
            position = orbit_calculator.calculate_position(elliptical_orbital_elements, time)
            velocity = orbit_calculator.calculate_velocity(elliptical_orbital_elements, time)
            
            r = np.linalg.norm(position)
            v = np.linalg.norm(velocity)
            a = elliptical_orbital_elements.semi_major_axis * orbit_calculator.au_to_m
            mu = orbit_calculator.gravitational_parameter
            
            # ビス・ビバ方程式: v² = μ(2/r - 1/a)
            expected_v_squared = mu * (2/r - 1/a)
            actual_v_squared = v**2
            
            relative_error = abs(actual_v_squared - expected_v_squared) / expected_v_squared
            assert relative_error < 0.001