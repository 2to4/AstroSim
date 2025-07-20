"""
太陽クラスの実装

太陽系の中心に位置する恒星としての太陽を表現します。
光源としての特性と固定位置を持ちます。
"""

import numpy as np
from typing import Dict, Any
from src.domain.celestial_body import CelestialBody


class Sun(CelestialBody):
    """
    太陽クラス
    
    太陽系の中心に位置する恒星として、
    光源特性と固定位置を持つ天体を表現します。
    """
    
    def __init__(
        self,
        name: str = "太陽",
        mass: float = 1.989e30,  # kg
        radius: float = 695700.0,  # km
        temperature: float = 5778.0,  # K
        luminosity: float = 3.828e26  # W
    ):
        """
        太陽の初期化
        
        Args:
            name: 太陽の名前
            mass: 質量 (kg)
            radius: 半径 (km)
            temperature: 表面温度 (K)
            luminosity: 光度 (W)
        """
        super().__init__(name, mass, radius)
        self.temperature = temperature
        self.luminosity = luminosity
        
        # 太陽は座標系の原点に固定
        self.position = np.zeros(3, dtype=np.float64)
        self.velocity = np.zeros(3, dtype=np.float64)
    
    def update_position(self, julian_date: float) -> None:
        """
        太陽の位置更新
        
        太陽は座標系の原点に固定されているため、
        位置は常に (0, 0, 0) のままです。
        
        Args:
            julian_date: ユリウス日（使用されない）
        """
        # 太陽は原点に固定
        self.position = np.zeros(3, dtype=np.float64)
        self.velocity = np.zeros(3, dtype=np.float64)
    
    def get_visual_properties(self) -> Dict[str, Any]:
        """
        太陽の視覚的プロパティを取得
        
        Returns:
            視覚プロパティの辞書
        """
        # 温度から色を計算（簡易的な黒体輻射近似）
        color = self._temperature_to_color(self.temperature)
        
        return {
            'color': color,
            'radius': self.radius,
            'temperature': self.temperature,
            'luminosity': self.luminosity,
            'is_light_source': True,
            'texture_path': None  # 太陽は発光体なのでテクスチャなし
        }
    
    def _temperature_to_color(self, temperature: float) -> tuple:
        """
        表面温度からRGB色を計算
        
        黒体輻射の近似を使用して、
        太陽の表面温度に対応する色を計算します。
        
        Args:
            temperature: 表面温度 (K)
            
        Returns:
            RGB色タプル (0.0-1.0)
        """
        # 太陽の温度（約5778K）は黄白色
        if temperature < 3500:
            return (1.0, 0.3, 0.0)  # 赤色矮星
        elif temperature < 5000:
            return (1.0, 0.7, 0.4)  # オレンジ色
        elif temperature < 6000:
            return (1.0, 1.0, 0.8)  # 黄色
        elif temperature < 7500:
            return (1.0, 1.0, 1.0)  # 白色
        else:
            return (0.8, 0.9, 1.0)  # 青白色
    
    def get_gravitational_influence_radius(self) -> float:
        """
        重力影響半径を計算
        
        太陽の重力が支配的な領域の半径を返します。
        
        Returns:
            重力影響半径 (AU)
        """
        # 太陽圏の半径（約100AU程度）
        return 100.0
    
    def get_escape_velocity(self) -> float:
        """
        太陽表面からの脱出速度を計算
        
        Returns:
            脱出速度 (km/s)
        """
        # 重力定数 (m³ kg⁻¹ s⁻²)
        G = 6.67430e-11
        
        # 脱出速度 = sqrt(2GM/r)
        radius_m = self.radius * 1000  # km -> m
        escape_velocity_ms = np.sqrt(2 * G * self.mass / radius_m)
        
        return escape_velocity_ms / 1000  # m/s -> km/s
    
    def to_dict(self) -> Dict[str, Any]:
        """
        太陽データを辞書形式に変換
        
        Returns:
            太陽データの辞書
        """
        return {
            'name': self.name,
            'mass': self.mass,
            'radius': self.radius,
            'temperature': self.temperature,
            'luminosity': self.luminosity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sun':
        """
        辞書から太陽オブジェクトを作成
        
        Args:
            data: 太陽データの辞書
            
        Returns:
            太陽オブジェクト
        """
        return cls(
            name=data.get('name', '太陽'),
            mass=data.get('mass', 1.989e30),
            radius=data.get('radius', 695700.0),
            temperature=data.get('temperature', 5778.0),
            luminosity=data.get('luminosity', 3.828e26)
        )
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.name} (温度: {self.temperature:.0f}K, 光度: {self.luminosity:.2e}W)"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (f"Sun(name='{self.name}', mass={self.mass}, radius={self.radius}, "
                f"temperature={self.temperature}, luminosity={self.luminosity})")