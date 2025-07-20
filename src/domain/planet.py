"""
惑星クラスの実装

軌道要素を持つ惑星の物理的性質と軌道運動を表現します。
ケプラーの法則に基づいて位置を計算します。
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from .celestial_body import CelestialBody
from .orbital_elements import OrbitalElements


class Planet(CelestialBody):
    """
    惑星クラス
    
    軌道要素を持ち、ケプラーの法則に基づいて
    太陽周りの軌道運動を行う天体を表現します。
    """
    
    def __init__(
        self,
        name: str,
        mass: float,
        radius: float,
        orbital_elements: OrbitalElements,
        color: Tuple[float, float, float],
        texture_path: Optional[str] = None,
        rotation_period: float = 24.0,
        axial_tilt: float = 0.0
    ):
        """
        惑星の初期化
        
        Args:
            name: 惑星名
            mass: 質量 (kg)
            radius: 半径 (km)
            orbital_elements: 軌道要素
            color: RGB色 (0.0-1.0)
            texture_path: テクスチャファイルパス
            rotation_period: 自転周期 (時間)
            axial_tilt: 自転軸傾斜角 (度)
        """
        super().__init__(name, mass, radius)
        self.orbital_elements = orbital_elements
        self.color = color
        self.texture_path = texture_path
        self.rotation_period = rotation_period
        self.axial_tilt = axial_tilt
        
        # 天文単位をkmに変換する係数
        self.AU_TO_KM = 149597870.7
        
        # 現在のユリウス日を追跡
        self.current_julian_date = orbital_elements.epoch
    
    def update_position(self, julian_date: float) -> None:
        """
        指定されたユリウス日での惑星位置を計算
        
        ケプラーの法則に基づいて軌道上の位置を求め、
        3次元座標系に変換します。
        
        Args:
            julian_date: ユリウス日
        """
        # 現在時刻を更新
        self.current_julian_date = julian_date
        # 元期からの経過時間（日）
        time_since_epoch = julian_date - self.orbital_elements.epoch
        
        # 平均近点角の計算
        mean_motion = 2 * np.pi / self.orbital_elements.get_orbital_period()
        mean_anomaly = (
            np.radians(self.orbital_elements.mean_anomaly_at_epoch) +
            mean_motion * time_since_epoch
        ) % (2 * np.pi)
        
        # 離心近点角の計算（ケプラー方程式の数値解）
        eccentric_anomaly = self._solve_kepler_equation(
            mean_anomaly, self.orbital_elements.eccentricity
        )
        
        # 真近点角の計算
        true_anomaly = self._calculate_true_anomaly(
            eccentric_anomaly, self.orbital_elements.eccentricity
        )
        
        # 軌道面での位置計算
        orbital_radius = self._calculate_orbital_radius(
            true_anomaly, self.orbital_elements
        )
        orbital_position = self._calculate_orbital_position(
            true_anomaly, orbital_radius
        )
        
        # 3次元空間座標への変換
        self.position = self._transform_to_heliocentric(
            orbital_position, self.orbital_elements
        )
    
    def _solve_kepler_equation(self, mean_anomaly: float, eccentricity: float) -> float:
        """
        ケプラー方程式を数値的に解く
        
        M = E - e*sin(E) を E について解く
        
        Args:
            mean_anomaly: 平均近点角 (ラジアン)
            eccentricity: 離心率
            
        Returns:
            離心近点角 (ラジアン)
        """
        # 初期推定値
        E = mean_anomaly
        
        # ニュートン・ラフソン法
        for _ in range(10):  # 最大10回の反復
            f = E - eccentricity * np.sin(E) - mean_anomaly
            f_prime = 1 - eccentricity * np.cos(E)
            
            delta_E = f / f_prime
            E -= delta_E
            
            # 収束判定
            if abs(delta_E) < 1e-12:
                break
        
        return E
    
    def _calculate_true_anomaly(self, eccentric_anomaly: float, eccentricity: float) -> float:
        """
        真近点角を計算
        
        Args:
            eccentric_anomaly: 離心近点角 (ラジアン)
            eccentricity: 離心率
            
        Returns:
            真近点角 (ラジアン)
        """
        cos_E = np.cos(eccentric_anomaly)
        sin_E = np.sin(eccentric_anomaly)
        
        cos_nu = (cos_E - eccentricity) / (1 - eccentricity * cos_E)
        sin_nu = (np.sqrt(1 - eccentricity**2) * sin_E) / (1 - eccentricity * cos_E)
        
        return np.arctan2(sin_nu, cos_nu)
    
    def _calculate_orbital_radius(self, true_anomaly: float, orbital_elements: OrbitalElements) -> float:
        """
        軌道半径を計算
        
        Args:
            true_anomaly: 真近点角 (ラジアン)
            orbital_elements: 軌道要素
            
        Returns:
            軌道半径 (km)
        """
        a = orbital_elements.semi_major_axis * self.AU_TO_KM
        e = orbital_elements.eccentricity
        
        return a * (1 - e**2) / (1 + e * np.cos(true_anomaly))
    
    def _calculate_orbital_position(self, true_anomaly: float, orbital_radius: float) -> np.ndarray:
        """
        軌道面での位置を計算
        
        Args:
            true_anomaly: 真近点角 (ラジアン)
            orbital_radius: 軌道半径 (km)
            
        Returns:
            軌道面での位置ベクトル (km)
        """
        x = orbital_radius * np.cos(true_anomaly)
        y = orbital_radius * np.sin(true_anomaly)
        
        return np.array([x, y])
    
    def _transform_to_heliocentric(self, orbital_position: np.ndarray, orbital_elements: OrbitalElements) -> np.ndarray:
        """
        軌道面座標から太陽中心座標系に変換
        
        Args:
            orbital_position: 軌道面での位置 (km)
            orbital_elements: 軌道要素
            
        Returns:
            太陽中心座標系での位置ベクトル (km)
        """
        # 角度をラジアンに変換
        i = np.radians(orbital_elements.inclination)
        omega = np.radians(orbital_elements.longitude_of_ascending_node)
        w = np.radians(orbital_elements.argument_of_perihelion)
        
        # 回転行列の計算
        cos_omega = np.cos(omega)
        sin_omega = np.sin(omega)
        cos_i = np.cos(i)
        sin_i = np.sin(i)
        cos_w = np.cos(w)
        sin_w = np.sin(w)
        
        # 3次元回転行列
        R11 = cos_omega * cos_w - sin_omega * sin_w * cos_i
        R12 = -cos_omega * sin_w - sin_omega * cos_w * cos_i
        R13 = sin_omega * sin_i
        
        R21 = sin_omega * cos_w + cos_omega * sin_w * cos_i
        R22 = -sin_omega * sin_w + cos_omega * cos_w * cos_i
        R23 = -cos_omega * sin_i
        
        R31 = sin_w * sin_i
        R32 = cos_w * sin_i
        R33 = cos_i
        
        # 軌道面座標を3次元に拡張
        x_orb, y_orb = orbital_position
        z_orb = 0.0
        
        # 座標変換
        x = R11 * x_orb + R12 * y_orb + R13 * z_orb
        y = R21 * x_orb + R22 * y_orb + R23 * z_orb
        z = R31 * x_orb + R32 * y_orb + R33 * z_orb
        
        return np.array([x, y, z])
    
    def _calculate_rotation_angle(self) -> float:
        """
        現在の自転角度を計算
        
        Returns:
            自転角度 (度)
        """
        # 現在時刻から自転角度を計算
        # ユリウス日から時間に変換（1日 = 24時間）
        current_time_hours = (self.current_julian_date - self.orbital_elements.epoch) * 24.0
        rotation_angle = (current_time_hours / self.rotation_period) * 360.0
        return rotation_angle % 360.0
    
    def get_visual_properties(self) -> Dict[str, Any]:
        """
        惑星の視覚的プロパティを取得
        
        Returns:
            視覚プロパティの辞書
        """
        return {
            'color': self.color,
            'texture_path': self.texture_path,
            'radius': self.radius,
            'rotation_angle': self._calculate_rotation_angle()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        惑星データを辞書形式に変換
        
        Returns:
            惑星データの辞書
        """
        return {
            'name': self.name,
            'mass': self.mass,
            'radius': self.radius,
            'color': self.color,
            'texture_path': self.texture_path,
            'rotation_period': self.rotation_period,
            'axial_tilt': self.axial_tilt,
            'orbital_elements': self.orbital_elements.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Planet':
        """
        辞書から惑星オブジェクトを作成
        
        Args:
            data: 惑星データの辞書
            
        Returns:
            惑星オブジェクト
        """
        orbital_elements = OrbitalElements.from_dict(data['orbital_elements'])
        
        return cls(
            name=data['name'],
            mass=data['mass'],
            radius=data['radius'],
            orbital_elements=orbital_elements,
            color=data['color'],
            texture_path=data.get('texture_path'),
            rotation_period=data.get('rotation_period', 24.0),
            axial_tilt=data.get('axial_tilt', 0.0)
        )
    
    def __eq__(self, other) -> bool:
        """等価性の比較"""
        if not isinstance(other, Planet):
            return False
        
        return (
            super().__eq__(other) and
            self.orbital_elements == other.orbital_elements and
            self.color == other.color
        )