"""
天体基底クラスの実装

全ての天体（惑星、太陽など）に共通する
基本的な物理的性質と動作を定義します。
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any


class CelestialBody(ABC):
    """
    天体の基底クラス
    
    全ての天体に共通する物理的性質と基本動作を定義します。
    具象クラスで位置更新と視覚プロパティを実装する必要があります。
    """
    
    def __init__(self, name: str, mass: float, radius: float):
        """
        天体の初期化
        
        Args:
            name: 天体名
            mass: 質量 (kg)
            radius: 半径 (km)
        """
        self.name = name
        self.mass = self._validate_mass(mass)
        self.radius = self._validate_radius(radius)
        self.position = np.zeros(3, dtype=np.float64)  # 位置ベクトル (km)
        self.velocity = np.zeros(3, dtype=np.float64)  # 速度ベクトル (km/s)
    
    def _validate_mass(self, mass: float) -> float:
        """質量の妥当性を検証"""
        if mass <= 0:
            raise ValueError("質量は正の値である必要があります")
        return mass
    
    def _validate_radius(self, radius: float) -> float:
        """半径の妥当性を検証"""
        if radius <= 0:
            raise ValueError("半径は正の値である必要があります")
        return radius
    
    @abstractmethod
    def update_position(self, julian_date: float) -> None:
        """
        指定されたユリウス日での位置を計算
        
        Args:
            julian_date: ユリウス日
        """
        pass
    
    @abstractmethod
    def get_visual_properties(self) -> Dict[str, Any]:
        """
        視覚的プロパティを取得
        
        Returns:
            視覚的プロパティの辞書
        """
        pass
    
    def distance_to(self, other: 'CelestialBody') -> float:
        """
        他の天体との距離を計算
        
        Args:
            other: 相手の天体
            
        Returns:
            距離 (km)
        """
        return np.linalg.norm(self.position - other.position)
    
    def gravitational_force_from(self, other: 'CelestialBody') -> np.ndarray:
        """
        他の天体からの重力を計算
        
        Args:
            other: 重力源となる天体
            
        Returns:
            重力ベクトル (m/s²)
        """
        # 重力定数 (m³ kg⁻¹ s⁻²)
        G = 6.67430e-11
        
        # 位置ベクトルの差 (kmをmに変換)
        r_vector = (other.position - self.position) * 1000  # km -> m
        r_magnitude = np.linalg.norm(r_vector)
        
        if r_magnitude == 0:
            raise ValueError("距離がゼロの天体間では重力計算できません")
        
        # 重力の大きさ
        force_magnitude = G * other.mass / (r_magnitude ** 2)
        
        # 重力の方向（単位ベクトル）
        force_direction = r_vector / r_magnitude
        
        return force_magnitude * force_direction
    
    def get_kinetic_energy(self) -> float:
        """
        運動エネルギーを計算
        
        Returns:
            運動エネルギー (J)
        """
        # 速度をm/sに変換
        velocity_ms = self.velocity * 1000  # km/s -> m/s
        speed_squared = np.dot(velocity_ms, velocity_ms)
        return 0.5 * self.mass * speed_squared
    
    def get_momentum(self) -> np.ndarray:
        """
        運動量を計算
        
        Returns:
            運動量ベクトル (kg⋅m/s)
        """
        # 速度をm/sに変換
        velocity_ms = self.velocity * 1000  # km/s -> m/s
        return self.mass * velocity_ms
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.name} (質量: {self.mass:.3e} kg, 半径: {self.radius:.1f} km)"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return f"CelestialBody(name='{self.name}', mass={self.mass}, radius={self.radius})"
    
    def __eq__(self, other) -> bool:
        """等価性の比較"""
        if not isinstance(other, CelestialBody):
            return False
        
        tolerance = 1e-10
        return (
            self.name == other.name and
            abs(self.mass - other.mass) < tolerance and
            abs(self.radius - other.radius) < tolerance
        )