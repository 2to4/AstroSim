"""
惑星クラスのテスト
"""

import pytest
import numpy as np
from src.domain.planet import Planet
from src.domain.orbital_elements import OrbitalElements


class TestPlanet:
    """惑星クラスのテスト"""
    
    def test_planet_initialization(self, earth_data):
        """惑星の初期化テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        assert planet.name == earth_data["name"]
        assert planet.mass == earth_data["mass"]
        assert planet.radius == earth_data["radius"]
        assert planet.orbital_elements == orbital_elements
        assert planet.color == earth_data["color"]
    
    def test_planet_initialization_with_optional_params(self, earth_data):
        """オプションパラメータ付きの初期化テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"],
            texture_path="earth.jpg",
            rotation_period=earth_data["physical_properties"]["rotation_period"],
            axial_tilt=earth_data["physical_properties"]["axial_tilt"]
        )
        
        assert planet.texture_path == "earth.jpg"
        assert planet.rotation_period == earth_data["physical_properties"]["rotation_period"]
        assert planet.axial_tilt == earth_data["physical_properties"]["axial_tilt"]
    
    def test_position_calculation_at_epoch(self, earth_data, approx):
        """元期での位置計算テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        # J2000.0 での位置計算
        planet.update_position(2451545.0)
        
        # 元期での位置は平均近点角から計算される
        # 具体的な値は軌道要素によるが、ゼロベクトルではないはず
        assert not np.allclose(planet.position, np.zeros(3))
        
        # 位置の大きさがほぼ軌道長半径と一致する（低離心率の場合）
        distance_from_sun = np.linalg.norm(planet.position)
        expected_distance = orbital_elements.semi_major_axis * 149597870.7  # AU to km
        
        # 離心率による変動を考慮して±10%の誤差を許容
        assert abs(distance_from_sun - expected_distance) / expected_distance < 0.1
    
    def test_position_calculation_circular_orbit(self):
        """円軌道での位置計算テスト"""
        # 完全円軌道の軌道要素
        circular_elements = OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.0,
            inclination=0.0,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0,
            epoch=2451545.0
        )
        
        planet = Planet(
            name="CircularPlanet",
            mass=1.0e24,
            radius=1000.0,
            orbital_elements=circular_elements,
            color=[1.0, 1.0, 1.0]
        )
        
        # 複数の時刻での位置計算
        times = [2451545.0, 2451545.0 + 91.3125, 2451545.0 + 182.625]  # 0, 1/4, 1/2年後
        positions = []
        
        for time in times:
            planet.update_position(time)
            positions.append(planet.position.copy())
        
        # 円軌道なので全ての位置で太陽からの距離が等しい
        distances = [np.linalg.norm(pos) for pos in positions]
        assert all(abs(d - distances[0]) < 1e-6 for d in distances)
    
    def test_position_calculation_elliptical_orbit(self):
        """楕円軌道での位置計算テスト"""
        # 楕円軌道の軌道要素
        elliptical_elements = OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.5,  # かなり楕円
            inclination=0.0,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0,
            epoch=2451545.0
        )
        
        planet = Planet(
            name="EllipticalPlanet",
            mass=1.0e24,
            radius=1000.0,
            orbital_elements=elliptical_elements,
            color=[1.0, 1.0, 1.0]
        )
        
        # 近日点と遠日点での位置計算
        # 近日点（平均近点角 = 0）
        planet.update_position(2451545.0)
        perihelion_distance = np.linalg.norm(planet.position)
        
        # 遠日点（平均近点角 = 180度に相当する時間後）
        half_period = 365.25 / 2  # 半年後
        planet.update_position(2451545.0 + half_period)
        aphelion_distance = np.linalg.norm(planet.position)
        
        # 楕円軌道の性質確認
        assert perihelion_distance < aphelion_distance
        
        # 理論値との比較
        expected_perihelion = elliptical_elements.semi_major_axis * (1 - elliptical_elements.eccentricity) * 149597870.7
        expected_aphelion = elliptical_elements.semi_major_axis * (1 + elliptical_elements.eccentricity) * 149597870.7
        
        assert abs(perihelion_distance - expected_perihelion) / expected_perihelion < 0.05
        assert abs(aphelion_distance - expected_aphelion) / expected_aphelion < 0.05
    
    @pytest.mark.parametrize("inclination,expected_z_motion", [
        (0.0, False),   # 軌道面がxy平面
        (90.0, True),   # 極軌道
        (30.0, True),   # 傾斜軌道
    ])
    def test_orbital_inclination_effect(self, inclination, expected_z_motion):
        """軌道傾斜角の影響テスト"""
        inclined_elements = OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.0,
            inclination=inclination,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0,
            epoch=2451545.0
        )
        
        planet = Planet(
            name="InclinedPlanet",
            mass=1.0e24,
            radius=1000.0,
            orbital_elements=inclined_elements,
            color=[1.0, 1.0, 1.0]
        )
        
        # 1/4周期分の位置を記録
        positions = []
        for i in range(5):
            time = 2451545.0 + i * 365.25 / 4
            planet.update_position(time)
            positions.append(planet.position.copy())
        
        # Z座標の変動をチェック
        z_coords = [pos[2] for pos in positions]
        z_variation = max(z_coords) - min(z_coords)
        
        if expected_z_motion:
            assert z_variation > 1e6  # 有意なZ方向の運動
        else:
            assert z_variation < 1e6  # Z方向の運動がほぼなし
    
    def test_orbital_period_consistency(self, earth_data):
        """軌道周期の一貫性テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        # 1周期後の位置
        start_time = 2451545.0
        period = orbital_elements.get_orbital_period()
        
        planet.update_position(start_time)
        initial_position = planet.position.copy()
        
        planet.update_position(start_time + period)
        final_position = planet.position.copy()
        
        # 1周期後の位置がほぼ同じであることを確認
        position_difference = np.linalg.norm(final_position - initial_position)
        orbit_size = np.linalg.norm(initial_position)
        
        # 軌道サイズに対して0.1%以下の誤差
        assert position_difference / orbit_size < 0.001
    
    def test_visual_properties(self, earth_data):
        """視覚プロパティのテスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"],
            texture_path="earth.jpg",
            rotation_period=24.0
        )
        
        properties = planet.get_visual_properties()
        
        assert properties['color'] == earth_data["color"]
        assert properties['texture_path'] == "earth.jpg"
        assert properties['radius'] == earth_data["radius"]
        assert 'rotation_angle' in properties
        assert isinstance(properties['rotation_angle'], float)
    
    def test_rotation_angle_calculation(self, earth_data):
        """自転角度の計算テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"],
            rotation_period=24.0  # 24時間で1回転
        )
        
        # 異なる時刻での自転角度
        planet.update_position(2451545.0)
        angle1 = planet._calculate_rotation_angle()
        
        planet.update_position(2451545.0 + 1.0)  # 1日後
        angle2 = planet._calculate_rotation_angle()
        
        # 1日で360度回転（modulo演算で0度になる）
        angle_difference = (angle2 - angle1) % 360
        # 360度回転は0度と等価なので、どちらかを許可
        assert abs(angle_difference) < 1e-6 or abs(angle_difference - 360.0) < 1e-6
    
    def test_planet_comparison(self, earth_data, mars_data):
        """惑星の比較テスト"""
        earth_elements = OrbitalElements(**earth_data["orbital_elements"])
        mars_elements = OrbitalElements(**mars_data["orbital_elements"])
        
        earth = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=earth_elements,
            color=earth_data["color"]
        )
        
        mars = Planet(
            name=mars_data["name"],
            mass=mars_data["mass"],
            radius=mars_data["radius"],
            orbital_elements=mars_elements,
            color=mars_data["color"]
        )
        
        # 異なる惑星は等しくない
        assert earth != mars
        
        # 火星の方が遠い軌道
        assert mars.orbital_elements.semi_major_axis > earth.orbital_elements.semi_major_axis
        
        # 地球の方が重い
        assert earth.mass > mars.mass
    
    def test_planet_from_dict(self, earth_data):
        """辞書からの惑星作成テスト"""
        planet = Planet.from_dict(earth_data)
        
        assert planet.name == earth_data["name"]
        assert planet.mass == earth_data["mass"]
        assert planet.radius == earth_data["radius"]
        assert isinstance(planet.orbital_elements, OrbitalElements)
    
    def test_planet_to_dict(self, earth_data):
        """惑星の辞書変換テスト"""
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        planet = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        planet_dict = planet.to_dict()
        
        assert planet_dict["name"] == earth_data["name"]
        assert planet_dict["mass"] == earth_data["mass"]
        assert planet_dict["radius"] == earth_data["radius"]
        assert "orbital_elements" in planet_dict
        assert planet_dict["color"] == earth_data["color"]