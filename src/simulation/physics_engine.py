"""
物理エンジンクラスの実装

軌道力学とN体問題の数値計算を行います。
重力計算、運動方程式の積分、ケプラー方程式の解などを提供します。
"""

import numpy as np
from typing import List, Tuple, Optional
from ..domain.celestial_body import CelestialBody


class PhysicsEngine:
    """
    物理シミュレーションエンジン
    
    軌道力学の計算、重力多体問題の数値積分、
    および関連する天体力学計算を担当します。
    """
    
    def __init__(self):
        """物理エンジンの初期化"""
        self.gravitational_constant: float = 6.67430e-11  # m³ kg⁻¹ s⁻²
        self.au_to_km: float = 149597870.7  # 天文単位からkmへの変換
        self.c_light: float = 299792458.0  # 光速 (m/s)
        
        # 数値計算の設定
        self.integration_method: str = "rk4"  # ルンゲ・クッタ4次
        self.convergence_tolerance: float = 1e-12
        self.max_iterations: int = 20
    
    def calculate_gravitational_force(self, 
                                    body1: CelestialBody, 
                                    body2: CelestialBody) -> np.ndarray:
        """
        2天体間の重力を計算
        
        Args:
            body1: 力を受ける天体
            body2: 力を及ぼす天体
            
        Returns:
            body1が受ける重力ベクトル (m/s²)
            
        Raises:
            ValueError: 天体間の距離がゼロの場合
        """
        # 位置ベクトルの差 (km -> m)
        r_vector = (body2.position - body1.position) * 1000
        r_magnitude = np.linalg.norm(r_vector)
        
        if r_magnitude == 0:
            raise ValueError("天体間の距離がゼロでは重力計算できません")
        
        # 重力の大きさ F = GMm/r²
        force_magnitude = (self.gravitational_constant * body2.mass) / (r_magnitude ** 2)
        
        # 重力の方向（単位ベクトル）
        force_direction = r_vector / r_magnitude
        
        return force_magnitude * force_direction
    
    def calculate_total_force(self, 
                            target_body: CelestialBody, 
                            other_bodies: List[CelestialBody]) -> np.ndarray:
        """
        1つの天体が他の全天体から受ける重力の合計を計算
        
        Args:
            target_body: 力を受ける天体
            other_bodies: 力を及ぼす天体のリスト
            
        Returns:
            合計重力ベクトル (m/s²)
        """
        total_force = np.zeros(3)
        
        for other_body in other_bodies:
            if other_body != target_body:
                force = self.calculate_gravitational_force(target_body, other_body)
                total_force += force
        
        return total_force
    
    def integrate_motion_rk4(self, 
                           bodies: List[CelestialBody], 
                           dt: float) -> None:
        """
        4次ルンゲ・クッタ法による運動方程式の数値積分
        
        Args:
            bodies: 天体のリスト
            dt: 時間ステップ (秒)
        """
        n = len(bodies)
        
        # 現在の状態を保存
        positions = np.array([body.position for body in bodies])  # km
        velocities = np.array([body.velocity for body in bodies])  # km/s
        
        # k1の計算
        k1_v = np.zeros((n, 3))
        k1_a = np.zeros((n, 3))
        
        for i, body in enumerate(bodies):
            k1_v[i] = velocities[i]
            k1_a[i] = self.calculate_total_force(body, bodies) / 1000  # m/s² -> km/s²
        
        # k2の計算
        for i, body in enumerate(bodies):
            body.position = positions[i] + 0.5 * dt * k1_v[i]
            body.velocity = velocities[i] + 0.5 * dt * k1_a[i]
        
        k2_v = np.zeros((n, 3))
        k2_a = np.zeros((n, 3))
        
        for i, body in enumerate(bodies):
            k2_v[i] = body.velocity
            k2_a[i] = self.calculate_total_force(body, bodies) / 1000
        
        # k3の計算
        for i, body in enumerate(bodies):
            body.position = positions[i] + 0.5 * dt * k2_v[i]
            body.velocity = velocities[i] + 0.5 * dt * k2_a[i]
        
        k3_v = np.zeros((n, 3))
        k3_a = np.zeros((n, 3))
        
        for i, body in enumerate(bodies):
            k3_v[i] = body.velocity
            k3_a[i] = self.calculate_total_force(body, bodies) / 1000
        
        # k4の計算
        for i, body in enumerate(bodies):
            body.position = positions[i] + dt * k3_v[i]
            body.velocity = velocities[i] + dt * k3_a[i]
        
        k4_v = np.zeros((n, 3))
        k4_a = np.zeros((n, 3))
        
        for i, body in enumerate(bodies):
            k4_v[i] = body.velocity
            k4_a[i] = self.calculate_total_force(body, bodies) / 1000
        
        # 最終的な位置と速度の更新
        for i, body in enumerate(bodies):
            body.position = positions[i] + (dt / 6) * (k1_v[i] + 2*k2_v[i] + 2*k3_v[i] + k4_v[i])
            body.velocity = velocities[i] + (dt / 6) * (k1_a[i] + 2*k2_a[i] + 2*k3_a[i] + k4_a[i])
    
    def solve_kepler_equation(self, 
                            mean_anomaly: float, 
                            eccentricity: float) -> float:
        """
        ケプラー方程式を数値的に解いて離心近点角を求める
        
        M = E - e*sin(E) をEについて解く
        
        Args:
            mean_anomaly: 平均近点角 (ラジアン)
            eccentricity: 離心率
            
        Returns:
            離心近点角 (ラジアン)
            
        Raises:
            ValueError: 収束しない場合
        """
        if not (0 <= eccentricity < 1):
            raise ValueError("離心率は0以上1未満である必要があります")
        
        # 初期推定値
        E = mean_anomaly
        
        # ニュートン・ラフソン法
        for iteration in range(self.max_iterations):
            f = E - eccentricity * np.sin(E) - mean_anomaly
            f_prime = 1 - eccentricity * np.cos(E)
            
            if abs(f_prime) < 1e-15:
                raise ValueError("ケプラー方程式の数値解法で発散しました")
            
            delta_E = f / f_prime
            E -= delta_E
            
            # 収束判定
            if abs(delta_E) < self.convergence_tolerance:
                return E
        
        raise ValueError(f"ケプラー方程式が{self.max_iterations}回の反復で収束しませんでした")
    
    def calculate_orbital_velocity(self, 
                                 position: np.ndarray, 
                                 central_mass: float) -> float:
        """
        軌道上の位置での速度を計算
        
        Args:
            position: 位置ベクトル (km)
            central_mass: 中心天体の質量 (kg)
            
        Returns:
            軌道速度の大きさ (km/s)
        """
        r = np.linalg.norm(position) * 1000  # km -> m
        
        # 円軌道速度 v = sqrt(GM/r)
        velocity_ms = np.sqrt(self.gravitational_constant * central_mass / r)
        
        return velocity_ms / 1000  # m/s -> km/s
    
    def calculate_escape_velocity(self, 
                                position: np.ndarray, 
                                central_mass: float) -> float:
        """
        脱出速度を計算
        
        Args:
            position: 位置ベクトル (km)
            central_mass: 中心天体の質量 (kg)
            
        Returns:
            脱出速度 (km/s)
        """
        r = np.linalg.norm(position) * 1000  # km -> m
        
        # 脱出速度 v = sqrt(2GM/r)
        velocity_ms = np.sqrt(2 * self.gravitational_constant * central_mass / r)
        
        return velocity_ms / 1000  # m/s -> km/s
    
    def calculate_orbital_energy(self, body: CelestialBody, central_mass: float) -> float:
        """
        軌道エネルギーを計算
        
        Args:
            body: 天体
            central_mass: 中心天体の質量 (kg)
            
        Returns:
            軌道エネルギー (J)
        """
        # 運動エネルギー
        kinetic_energy = body.get_kinetic_energy()
        
        # ポテンシャルエネルギー
        r = np.linalg.norm(body.position) * 1000  # km -> m
        potential_energy = -self.gravitational_constant * body.mass * central_mass / r
        
        return kinetic_energy + potential_energy
    
    def calculate_hill_sphere_radius(self, 
                                   body_mass: float, 
                                   central_mass: float, 
                                   semi_major_axis: float) -> float:
        """
        ヒル球半径を計算
        
        Args:
            body_mass: 天体の質量 (kg)
            central_mass: 中心天体の質量 (kg)
            semi_major_axis: 軌道長半径 (AU)
            
        Returns:
            ヒル球半径 (km)
        """
        a_km = semi_major_axis * self.au_to_km
        
        # ヒル球半径 r_H = a * (m/(3M))^(1/3)
        hill_radius = a_km * ((body_mass / (3 * central_mass)) ** (1/3))
        
        return hill_radius
    
    def calculate_tidal_force_gradient(self, 
                                     body1: CelestialBody, 
                                     body2: CelestialBody) -> np.ndarray:
        """
        潮汐力勾配を計算
        
        Args:
            body1: 潮汐力を受ける天体
            body2: 潮汐力を及ぼす天体
            
        Returns:
            潮汐力勾配テンソル (m/s²/m)
        """
        r_vector = (body2.position - body1.position) * 1000  # km -> m
        r = np.linalg.norm(r_vector)
        
        if r == 0:
            return np.zeros((3, 3))
        
        # 潮汐力勾配 = -GM/r³ * (3 * r̂r̂ - I)
        unit_vector = r_vector / r
        outer_product = np.outer(unit_vector, unit_vector)
        identity = np.eye(3)
        
        gradient = -(self.gravitational_constant * body2.mass / r**3) * (3 * outer_product - identity)
        
        return gradient
    
    def get_system_total_energy(self, bodies: List[CelestialBody]) -> float:
        """
        系全体の全エネルギーを計算
        
        Args:
            bodies: 天体のリスト
            
        Returns:
            全エネルギー (J)
        """
        total_kinetic = 0.0
        total_potential = 0.0
        
        # 運動エネルギー
        for body in bodies:
            total_kinetic += body.get_kinetic_energy()
        
        # ポテンシャルエネルギー
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                r = body1.distance_to(body2) * 1000  # km -> m
                if r > 0:
                    potential = -self.gravitational_constant * body1.mass * body2.mass / r
                    total_potential += potential
        
        return total_kinetic + total_potential
    
    def get_system_angular_momentum(self, bodies: List[CelestialBody]) -> np.ndarray:
        """
        系全体の角運動量を計算
        
        Args:
            bodies: 天体のリスト
            
        Returns:
            全角運動量ベクトル (kg⋅m²/s)
        """
        total_angular_momentum = np.zeros(3)
        
        for body in bodies:
            # 位置と運動量ベクトル
            r = body.position * 1000  # km -> m
            p = body.get_momentum()
            
            # 角運動量 L = r × p
            angular_momentum = np.cross(r, p)
            total_angular_momentum += angular_momentum
        
        return total_angular_momentum
    
    def set_integration_method(self, method: str) -> None:
        """
        数値積分法を設定
        
        Args:
            method: 積分法 ("rk4", "euler", "verlet")
        """
        valid_methods = ["rk4", "euler", "verlet"]
        if method not in valid_methods:
            raise ValueError(f"無効な積分法です: {method}. 有効な値: {valid_methods}")
        
        self.integration_method = method
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"PhysicsEngine (積分法: {self.integration_method}, 許容誤差: {self.convergence_tolerance})"