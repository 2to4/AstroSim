"""
太陽系クラスの実装

太陽系全体を管理し、太陽と惑星群の
集合体としての動作を提供します。
"""

import numpy as np
from typing import Dict, List, Optional, Any
from .celestial_body import CelestialBody
from .sun import Sun
from .planet import Planet


class SolarSystem:
    """
    太陽系クラス
    
    太陽と惑星群を管理し、太陽系全体としての
    シミュレーションと状態管理を行います。
    """
    
    def __init__(self):
        """太陽系の初期化"""
        self.sun: Optional[Sun] = None
        self.planets: Dict[str, Planet] = {}
        self.current_date: float = 0.0  # ユリウス日
    
    def add_celestial_body(self, body: CelestialBody) -> None:
        """
        天体を太陽系に追加
        
        Args:
            body: 追加する天体
            
        Raises:
            ValueError: 同名の惑星が既に存在する場合
        """
        if isinstance(body, Sun):
            self.sun = body
        elif isinstance(body, Planet):
            if body.name in self.planets:
                raise ValueError(f"惑星 '{body.name}' は既に存在します")
            self.planets[body.name] = body
        else:
            raise TypeError("太陽系に追加できるのは Sun または Planet のみです")
    
    def get_planet_by_name(self, name: str) -> Optional[Planet]:
        """
        名前で惑星を検索
        
        Args:
            name: 惑星名
            
        Returns:
            見つかった惑星、存在しない場合は None
        """
        return self.planets.get(name)
    
    def update_all_positions(self, julian_date: float) -> None:
        """
        全天体の位置を更新
        
        Args:
            julian_date: ユリウス日
        """
        self.current_date = julian_date
        
        # 太陽の位置更新（原点に固定）
        if self.sun:
            self.sun.update_position(julian_date)
        
        # 全惑星の位置更新
        for planet in self.planets.values():
            planet.update_position(julian_date)
    
    def get_all_bodies(self) -> List[CelestialBody]:
        """
        全天体のリストを取得
        
        Returns:
            全天体のリスト
        """
        bodies = []
        
        if self.sun:
            bodies.append(self.sun)
        
        bodies.extend(self.planets.values())
        
        return bodies
    
    def get_planets_list(self) -> List[Planet]:
        """
        惑星のリストを取得
        
        Returns:
            惑星のリスト
        """
        return list(self.planets.values())
    
    def get_system_bounds(self) -> Dict[str, float]:
        """
        太陽系の境界を計算
        
        Returns:
            境界座標の辞書 (min_x, max_x, min_y, max_y, min_z, max_z)
        """
        if not self.planets:
            return {
                'min_x': 0.0, 'max_x': 0.0,
                'min_y': 0.0, 'max_y': 0.0,
                'min_z': 0.0, 'max_z': 0.0
            }
        
        # 全惑星の位置から境界を計算
        positions = np.array([planet.position for planet in self.planets.values()])
        
        return {
            'min_x': float(np.min(positions[:, 0])),
            'max_x': float(np.max(positions[:, 0])),
            'min_y': float(np.min(positions[:, 1])),
            'max_y': float(np.max(positions[:, 1])),
            'min_z': float(np.min(positions[:, 2])),
            'max_z': float(np.max(positions[:, 2]))
        }
    
    def get_center_of_mass(self) -> np.ndarray:
        """
        太陽系の質量中心を計算
        
        Returns:
            質量中心の位置ベクトル (km)
        """
        total_mass = 0.0
        weighted_position = np.zeros(3)
        
        # 太陽の寄与
        if self.sun:
            total_mass += self.sun.mass
            weighted_position += self.sun.mass * self.sun.position
        
        # 惑星の寄与
        for planet in self.planets.values():
            total_mass += planet.mass
            weighted_position += planet.mass * planet.position
        
        if total_mass == 0:
            return np.zeros(3)
        
        return weighted_position / total_mass
    
    def get_total_energy(self) -> float:
        """
        太陽系の全エネルギーを計算
        
        Returns:
            全エネルギー (J)
        """
        total_kinetic = 0.0
        total_potential = 0.0
        
        bodies = self.get_all_bodies()
        
        # 運動エネルギーの計算
        for body in bodies:
            total_kinetic += body.get_kinetic_energy()
        
        # ポテンシャルエネルギーの計算
        G = 6.67430e-11  # 重力定数
        
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                r = body1.distance_to(body2) * 1000  # km -> m
                if r > 0:
                    potential_energy = -G * body1.mass * body2.mass / r
                    total_potential += potential_energy
        
        return total_kinetic + total_potential
    
    def get_angular_momentum(self) -> np.ndarray:
        """
        太陽系の全角運動量を計算
        
        Returns:
            角運動量ベクトル (kg⋅m²/s)
        """
        total_angular_momentum = np.zeros(3)
        
        bodies = self.get_all_bodies()
        
        for body in bodies:
            # 位置と運動量ベクトル
            r = body.position * 1000  # km -> m
            p = body.get_momentum()
            
            # 角運動量 L = r × p
            angular_momentum = np.cross(r, p)
            total_angular_momentum += angular_momentum
        
        return total_angular_momentum
    
    def to_dict(self) -> Dict[str, Any]:
        """
        太陽系データを辞書形式に変換
        
        Returns:
            太陽系データの辞書
        """
        data = {
            'current_date': self.current_date,
            'planets': [planet.to_dict() for planet in self.planets.values()]
        }
        
        if self.sun:
            data['sun'] = self.sun.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolarSystem':
        """
        辞書から太陽系オブジェクトを作成
        
        Args:
            data: 太陽系データの辞書
            
        Returns:
            太陽系オブジェクト
        """
        solar_system = cls()
        solar_system.current_date = data.get('current_date', 0.0)
        
        # 太陽の復元
        if 'sun' in data:
            solar_system.sun = Sun.from_dict(data['sun'])
        
        # 惑星の復元
        for planet_data in data.get('planets', []):
            planet = Planet.from_dict(planet_data)
            solar_system.planets[planet.name] = planet
        
        return solar_system
    
    def get_planet_count(self) -> int:
        """惑星数を取得"""
        return len(self.planets)
    
    def has_sun(self) -> bool:
        """太陽が存在するかチェック"""
        return self.sun is not None
    
    def clear(self) -> None:
        """太陽系をクリア"""
        self.sun = None
        self.planets.clear()
        self.current_date = 0.0
    
    def __len__(self) -> int:
        """天体数を返す"""
        count = len(self.planets)
        if self.sun:
            count += 1
        return count
    
    def __str__(self) -> str:
        """文字列表現"""
        body_count = len(self)
        planet_names = list(self.planets.keys())
        
        if len(planet_names) <= 3:
            planet_str = ", ".join(planet_names)
        else:
            planet_str = f"{', '.join(planet_names[:3])}...他{len(planet_names)-3}個"
        
        return f"太陽系 ({body_count}天体: {planet_str})"