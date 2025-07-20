"""
天体基底クラスのテスト
"""

import pytest
import numpy as np
from abc import ABC
from src.domain.celestial_body import CelestialBody


class ConcreteCelestialBody(CelestialBody):
    """テスト用の具象天体クラス"""
    
    def update_position(self, julian_date: float) -> None:
        """テスト用の位置更新実装"""
        # 簡単な円運動をシミュレート
        t = julian_date - 2451545.0  # J2000からの経過日数
        angle = 2 * np.pi * t / 365.25  # 1年で1周
        self.position = np.array([np.cos(angle), np.sin(angle), 0.0]) * 10.0
    
    def get_visual_properties(self) -> dict:
        """テスト用の視覚プロパティ"""
        return {
            'color': [1.0, 1.0, 1.0],
            'radius': self.radius,
            'texture': None
        }


class TestCelestialBody:
    """天体基底クラスのテスト"""
    
    def test_celestial_body_initialization(self):
        """天体の基本初期化テスト"""
        name = "TestBody"
        mass = 1.0e24
        radius = 1000.0
        
        body = ConcreteCelestialBody(name, mass, radius)
        
        assert body.name == name
        assert body.mass == mass
        assert body.radius == radius
        assert np.array_equal(body.position, np.zeros(3))
        assert np.array_equal(body.velocity, np.zeros(3))
    
    def test_celestial_body_is_abstract(self):
        """基底クラスが抽象クラスであることを確認"""
        assert issubclass(CelestialBody, ABC)
        
        # 直接インスタンス化できないことを確認
        with pytest.raises(TypeError):
            CelestialBody("test", 1.0, 1.0)
    
    @pytest.mark.parametrize("mass,expected_valid", [
        (1.0e20, True),   # 小さな天体
        (1.0e30, True),   # 恒星質量
        (0.0, False),     # ゼロ質量
        (-1.0, False),    # 負の質量
    ])
    def test_mass_validation(self, mass, expected_valid):
        """質量の妥当性検証"""
        if expected_valid:
            body = ConcreteCelestialBody("test", mass, 1000.0)
            assert body.mass == mass
        else:
            with pytest.raises(ValueError, match="質量"):
                ConcreteCelestialBody("test", mass, 1000.0)
    
    @pytest.mark.parametrize("radius,expected_valid", [
        (1.0, True),      # 小さな天体
        (696000.0, True), # 太陽サイズ
        (0.0, False),     # ゼロ半径
        (-100.0, False),  # 負の半径
    ])
    def test_radius_validation(self, radius, expected_valid):
        """半径の妥当性検証"""
        if expected_valid:
            body = ConcreteCelestialBody("test", 1.0e24, radius)
            assert body.radius == radius
        else:
            with pytest.raises(ValueError, match="半径"):
                ConcreteCelestialBody("test", 1.0e24, radius)
    
    def test_position_setter_getter(self):
        """位置の設定と取得テスト"""
        body = ConcreteCelestialBody("test", 1.0e24, 1000.0)
        
        new_position = np.array([100.0, 200.0, 300.0])
        body.position = new_position
        
        assert np.array_equal(body.position, new_position)
    
    def test_velocity_setter_getter(self):
        """速度の設定と取得テスト"""
        body = ConcreteCelestialBody("test", 1.0e24, 1000.0)
        
        new_velocity = np.array([10.0, 20.0, 30.0])
        body.velocity = new_velocity
        
        assert np.array_equal(body.velocity, new_velocity)
    
    def test_position_update(self):
        """位置更新機能のテスト"""
        body = ConcreteCelestialBody("test", 1.0e24, 1000.0)
        
        # 初期位置
        initial_position = body.position.copy()
        
        # 位置更新
        body.update_position(2451545.0)  # J2000
        
        # 位置が変更されていることを確認
        assert not np.array_equal(body.position, initial_position)
        
        # 期待される位置（円運動の開始位置）
        expected_position = np.array([10.0, 0.0, 0.0])
        assert np.allclose(body.position, expected_position, atol=1e-10)
    
    def test_distance_calculation(self):
        """天体間距離の計算テスト"""
        body1 = ConcreteCelestialBody("body1", 1.0e24, 1000.0)
        body2 = ConcreteCelestialBody("body2", 1.0e24, 1000.0)
        
        body1.position = np.array([0.0, 0.0, 0.0])
        body2.position = np.array([3.0, 4.0, 0.0])
        
        distance = body1.distance_to(body2)
        expected_distance = 5.0  # 3-4-5 直角三角形
        
        assert abs(distance - expected_distance) < 1e-10
    
    def test_gravitational_force_calculation(self, math_constants):
        """重力加速度計算のテスト（実装は加速度を返す）"""
        body1 = ConcreteCelestialBody("body1", 1.0e24, 1000.0)
        body2 = ConcreteCelestialBody("body2", 2.0e24, 1000.0)
        
        body1.position = np.array([0.0, 0.0, 0.0])
        body2.position = np.array([1000.0, 0.0, 0.0])  # 1000km離れた位置
        
        acceleration = body1.gravitational_force_from(body2)
        
        # 重力加速度の大きさを計算（実装は加速度 m/s² を返す）
        distance = 1000.0 * 1000  # km -> m
        expected_magnitude = math_constants["G"] * body2.mass / (distance ** 2)
        
        acceleration_magnitude = np.linalg.norm(acceleration)
        assert abs(acceleration_magnitude - expected_magnitude) / expected_magnitude < 1e-10
        
        # 加速度の方向が正しいことを確認（body2方向）
        expected_direction = np.array([1.0, 0.0, 0.0])
        actual_direction = acceleration / acceleration_magnitude
        assert np.allclose(actual_direction, expected_direction, atol=1e-10)
    
    def test_kinetic_energy(self):
        """運動エネルギーの計算テスト"""
        body = ConcreteCelestialBody("test", 2.0e24, 1000.0)
        body.velocity = np.array([1000.0, 0.0, 0.0])  # 1000 km/s
        
        kinetic_energy = body.get_kinetic_energy()
        # 実装では速度をkm/s→m/sに変換するため、1000 km/s = 1,000,000 m/s
        velocity_ms = 1000.0 * 1000  # km/s -> m/s
        expected_energy = 0.5 * body.mass * (velocity_ms ** 2)  # J
        
        assert abs(kinetic_energy - expected_energy) < 1e-10
    
    def test_momentum(self):
        """運動量の計算テスト"""
        body = ConcreteCelestialBody("test", 1.0e24, 1000.0)
        body.velocity = np.array([500.0, 300.0, 0.0])  # km/s
        
        momentum = body.get_momentum()
        # 実装では速度をkm/s→m/sに変換するため
        velocity_ms = body.velocity * 1000  # km/s -> m/s
        expected_momentum = body.mass * velocity_ms
        
        assert np.allclose(momentum, expected_momentum, atol=1e-10)
    
    def test_string_representation(self):
        """文字列表現のテスト"""
        body = ConcreteCelestialBody("TestPlanet", 5.972e24, 6371.0)
        
        str_repr = str(body)
        assert "TestPlanet" in str_repr
        assert "5.972e+24" in str_repr or "5.972e24" in str_repr
        assert "6371.0" in str_repr
    
    def test_equality(self):
        """等価性の比較テスト"""
        body1 = ConcreteCelestialBody("Earth", 5.972e24, 6371.0)
        body2 = ConcreteCelestialBody("Earth", 5.972e24, 6371.0)
        body3 = ConcreteCelestialBody("Mars", 6.39e23, 3389.5)
        
        assert body1 == body2
        assert body1 != body3
        assert not (body1 == "not a celestial body")
    
    def test_visual_properties_interface(self):
        """視覚プロパティインターフェースのテスト"""
        body = ConcreteCelestialBody("test", 1.0e24, 1000.0)
        
        properties = body.get_visual_properties()
        
        assert isinstance(properties, dict)
        assert 'color' in properties
        assert 'radius' in properties
        assert properties['radius'] == body.radius