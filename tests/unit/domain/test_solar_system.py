"""
太陽系クラスのテスト
"""

import pytest
import numpy as np
from src.domain.solar_system import SolarSystem
from src.domain.sun import Sun
from src.domain.planet import Planet
from src.domain.orbital_elements import OrbitalElements


class TestSolarSystem:
    """太陽系クラスのテスト"""
    
    def test_solar_system_initialization(self):
        """太陽系の初期化テスト"""
        solar_system = SolarSystem()
        
        assert solar_system.sun is None
        assert len(solar_system.planets) == 0
        assert solar_system.current_date == 0.0
    
    def test_add_sun(self):
        """太陽の追加テスト"""
        solar_system = SolarSystem()
        sun = Sun(
            name="太陽",
            mass=1.989e30,
            radius=695700.0,
            temperature=5778.0,
            luminosity=3.828e26
        )
        
        solar_system.add_celestial_body(sun)
        
        assert solar_system.sun is sun
        assert isinstance(solar_system.sun, Sun)
    
    def test_add_planet(self, earth_data):
        """惑星の追加テスト"""
        solar_system = SolarSystem()
        
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        earth = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        solar_system.add_celestial_body(earth)
        
        assert earth_data["name"] in solar_system.planets
        assert solar_system.planets[earth_data["name"]] is earth
    
    def test_add_multiple_planets(self, test_solar_system_data):
        """複数惑星の追加テスト"""
        solar_system = SolarSystem()
        
        # 太陽の追加
        sun_data = test_solar_system_data["sun"]
        sun = Sun(
            name=sun_data["name"],
            mass=sun_data["mass"],
            radius=sun_data["radius"],
            temperature=5778.0,
            luminosity=3.828e26
        )
        solar_system.add_celestial_body(sun)
        
        # 惑星の追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        assert len(solar_system.planets) == 2  # 水星と金星
        assert "水星" in solar_system.planets
        assert "金星" in solar_system.planets
        assert solar_system.sun is sun
    
    def test_duplicate_planet_handling(self, earth_data):
        """重複惑星の処理テスト"""
        solar_system = SolarSystem()
        
        orbital_elements = OrbitalElements(**earth_data["orbital_elements"])
        earth1 = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        earth2 = Planet(
            name=earth_data["name"],  # 同じ名前
            mass=earth_data["mass"] * 2,  # 異なる質量
            radius=earth_data["radius"],
            orbital_elements=orbital_elements,
            color=earth_data["color"]
        )
        
        solar_system.add_celestial_body(earth1)
        
        # 同じ名前の惑星を追加しようとした場合の処理
        with pytest.raises(ValueError, match="既に存在"):
            solar_system.add_celestial_body(earth2)
    
    def test_get_planet_by_name(self, earth_data, mars_data):
        """名前による惑星検索テスト"""
        solar_system = SolarSystem()
        
        # 地球と火星を追加
        earth_elements = OrbitalElements(**earth_data["orbital_elements"])
        earth = Planet(
            name=earth_data["name"],
            mass=earth_data["mass"],
            radius=earth_data["radius"],
            orbital_elements=earth_elements,
            color=earth_data["color"]
        )
        
        mars_elements = OrbitalElements(**mars_data["orbital_elements"])
        mars = Planet(
            name=mars_data["name"],
            mass=mars_data["mass"],
            radius=mars_data["radius"],
            orbital_elements=mars_elements,
            color=mars_data["color"]
        )
        
        solar_system.add_celestial_body(earth)
        solar_system.add_celestial_body(mars)
        
        # 正常な検索
        found_earth = solar_system.get_planet_by_name("地球")
        found_mars = solar_system.get_planet_by_name("火星")
        
        assert found_earth is earth
        assert found_mars is mars
        
        # 存在しない惑星の検索
        not_found = solar_system.get_planet_by_name("存在しない惑星")
        assert not_found is None
    
    def test_update_all_positions(self, test_solar_system_data, j2000_epoch):
        """全天体位置更新テスト"""
        solar_system = SolarSystem()
        
        # 惑星を追加
        planets = []
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
            planets.append(planet)
        
        # 初期位置を記録
        initial_positions = {}
        for planet in planets:
            initial_positions[planet.name] = planet.position.copy()
        
        # 位置更新
        future_date = j2000_epoch + 100.0  # 100日後
        solar_system.update_all_positions(future_date)
        
        # 全ての惑星の位置が更新されていることを確認
        for planet in planets:
            assert not np.allclose(planet.position, initial_positions[planet.name])
        
        # 現在日時が更新されていることを確認
        assert solar_system.current_date == future_date
    
    def test_get_all_bodies(self, test_solar_system_data):
        """全天体取得テスト"""
        solar_system = SolarSystem()
        
        # 太陽の追加
        sun_data = test_solar_system_data["sun"]
        sun = Sun(
            name=sun_data["name"],
            mass=sun_data["mass"],
            radius=sun_data["radius"],
            temperature=5778.0,
            luminosity=3.828e26
        )
        solar_system.add_celestial_body(sun)
        
        # 惑星の追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        all_bodies = solar_system.get_all_bodies()
        
        # 太陽 + 2惑星 = 3天体
        assert len(all_bodies) == 3
        
        # 太陽が含まれている
        assert sun in all_bodies
        
        # 全ての惑星が含まれている
        planet_names = [body.name for body in all_bodies if hasattr(body, 'orbital_elements')]
        assert "水星" in planet_names
        assert "金星" in planet_names
    
    def test_get_planets_list(self, test_solar_system_data):
        """惑星リスト取得テスト"""
        solar_system = SolarSystem()
        
        # 惑星の追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        planets_list = solar_system.get_planets_list()
        
        assert len(planets_list) == 2
        assert all(isinstance(planet, Planet) for planet in planets_list)
        
        planet_names = [planet.name for planet in planets_list]
        assert "水星" in planet_names
        assert "金星" in planet_names
    
    def test_solar_system_bounds(self, test_solar_system_data, j2000_epoch):
        """太陽系の境界計算テスト"""
        solar_system = SolarSystem()
        
        # 惑星を追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        # 位置更新
        solar_system.update_all_positions(j2000_epoch)
        
        # 境界計算
        bounds = solar_system.get_system_bounds()
        
        assert 'min_x' in bounds
        assert 'max_x' in bounds
        assert 'min_y' in bounds
        assert 'max_y' in bounds
        assert 'min_z' in bounds
        assert 'max_z' in bounds
        
        # 最小値 < 最大値
        assert bounds['min_x'] <= bounds['max_x']
        assert bounds['min_y'] <= bounds['max_y']
        assert bounds['min_z'] <= bounds['max_z']
    
    def test_center_of_mass(self, test_solar_system_data):
        """質量中心計算テスト"""
        solar_system = SolarSystem()
        
        # 太陽の追加
        sun_data = test_solar_system_data["sun"]
        sun = Sun(
            name=sun_data["name"],
            mass=sun_data["mass"],
            radius=sun_data["radius"],
            temperature=5778.0,
            luminosity=3.828e26
        )
        solar_system.add_celestial_body(sun)
        
        # 惑星の追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        # 位置更新
        solar_system.update_all_positions(2451545.0)
        
        # 質量中心計算
        center_of_mass = solar_system.get_center_of_mass()
        
        # 太陽が圧倒的に重いため、質量中心は太陽の近くにある
        assert isinstance(center_of_mass, np.ndarray)
        assert len(center_of_mass) == 3
        
        # 質量中心が太陽から大きく離れていないことを確認
        sun_position = np.array([0.0, 0.0, 0.0])  # 太陽は原点
        distance_from_sun = np.linalg.norm(center_of_mass - sun_position)
        
        # 太陽半径の数倍以内
        assert distance_from_sun < sun.radius * 10
    
    def test_empty_solar_system(self):
        """空の太陽系の処理テスト"""
        solar_system = SolarSystem()
        
        # 空の状態での操作
        assert solar_system.get_planet_by_name("地球") is None
        assert len(solar_system.get_all_bodies()) == 0
        assert len(solar_system.get_planets_list()) == 0
        
        # 位置更新は何もしない
        solar_system.update_all_positions(2451545.0)
        assert solar_system.current_date == 2451545.0
    
    def test_solar_system_serialization(self, test_solar_system_data):
        """太陽系のシリアライゼーションテスト"""
        solar_system = SolarSystem()
        
        # 惑星を追加
        for planet_data in test_solar_system_data["planets"]:
            orbital_elements = OrbitalElements(**planet_data["orbital_elements"])
            planet = Planet(
                name=planet_data["name"],
                mass=planet_data["mass"],
                radius=planet_data["radius"],
                orbital_elements=orbital_elements,
                color=planet_data["color"]
            )
            solar_system.add_celestial_body(planet)
        
        # 辞書変換
        solar_system_dict = solar_system.to_dict()
        
        assert "planets" in solar_system_dict
        assert len(solar_system_dict["planets"]) == 2
        assert "current_date" in solar_system_dict
        
        # 辞書から復元
        restored_solar_system = SolarSystem.from_dict(solar_system_dict)
        
        assert len(restored_solar_system.planets) == 2
        assert "水星" in restored_solar_system.planets
        assert "金星" in restored_solar_system.planets