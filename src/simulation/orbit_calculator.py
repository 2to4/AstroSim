"""
軌道計算クラスの実装

ケプラー軌道要素から位置・速度を計算し、
軌道の性質を分析する機能を提供します。
"""

import numpy as np
import hashlib
from typing import Tuple, Dict, Optional, List
from ..domain.orbital_elements import OrbitalElements
from ..domain.celestial_body import CelestialBody


class OrbitCalculator:
    """
    軌道計算クラス
    
    ケプラー軌道要素に基づく位置・速度計算、
    軌道の分析、軌道要素の相互変換などを行います。
    """
    
    def __init__(self):
        """軌道計算機の初期化"""
        self.gravitational_constant = 6.67430e-11  # m³ kg⁻¹ s⁻²
        self.au_to_km = 149597870.7  # 天文単位 -> km
        self.solar_mass = 1.989e30  # 太陽質量 (kg)
        
        # 数値計算設定
        self.convergence_tolerance = 1e-12
        self.max_iterations = 50
        
        # 軌道計算キャッシュ
        self.position_cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.cache_max_size = 10000  # 最大キャッシュサイズ
        self.cache_time_tolerance = 0.01  # 時間の許容誤差（日）
    
    def calculate_position_velocity(self, 
                                  orbital_elements: OrbitalElements,
                                  julian_date: float,
                                  central_mass: float = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        軌道要素から位置と速度を計算（キャッシュ機能付き）
        
        Args:
            orbital_elements: 軌道要素
            julian_date: ユリウス日
            central_mass: 中心天体質量 (kg)、Noneの場合は太陽質量を使用
            
        Returns:
            (位置ベクトル(km), 速度ベクトル(km/s))
        """
        if central_mass is None:
            central_mass = self.solar_mass
        
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(orbital_elements, julian_date, central_mass)
        
        # キャッシュから検索
        cached_result = self._get_from_cache(cache_key, julian_date)
        if cached_result is not None:
            self.cache_hit_count += 1
            return cached_result
        
        self.cache_miss_count += 1
        
        # 元期からの経過時間
        time_since_epoch = julian_date - orbital_elements.epoch
        
        # 平均近点角の計算
        mean_motion = self._calculate_mean_motion(orbital_elements, central_mass)
        mean_anomaly = (
            np.radians(orbital_elements.mean_anomaly_at_epoch) +
            mean_motion * time_since_epoch
        ) % (2 * np.pi)
        
        # 離心近点角の計算
        eccentric_anomaly = self._solve_kepler_equation(
            mean_anomaly, orbital_elements.eccentricity
        )
        
        # 真近点角の計算
        true_anomaly = self._calculate_true_anomaly(
            eccentric_anomaly, orbital_elements.eccentricity
        )
        
        # 軌道半径
        orbital_radius = self._calculate_orbital_radius(
            true_anomaly, orbital_elements
        )
        
        # 軌道面での位置と速度
        orbital_position = self._calculate_orbital_position(true_anomaly, orbital_radius)
        orbital_velocity = self._calculate_orbital_velocity(
            true_anomaly, orbital_elements, central_mass
        )
        
        # 3次元空間座標への変換
        position = self._transform_to_heliocentric(orbital_position, orbital_elements)
        velocity = self._transform_velocity_to_heliocentric(
            orbital_velocity, true_anomaly, orbital_elements
        )
        
        # 結果をキャッシュに保存
        result = (position, velocity)
        self._store_in_cache(cache_key, result, julian_date)
        
        return result
    
    def _generate_cache_key(self, 
                          orbital_elements: OrbitalElements, 
                          julian_date: float, 
                          central_mass: float) -> str:
        """
        キャッシュキーを生成
        
        Args:
            orbital_elements: 軌道要素
            julian_date: ユリウス日
            central_mass: 中心天体質量
            
        Returns:
            キャッシュキー
        """
        # 軌道要素のハッシュを生成
        elements_str = (
            f"{orbital_elements.semi_major_axis:.10f}_"
            f"{orbital_elements.eccentricity:.10f}_"
            f"{orbital_elements.inclination:.6f}_"
            f"{orbital_elements.longitude_of_ascending_node:.6f}_"
            f"{orbital_elements.argument_of_perihelion:.6f}_"
            f"{orbital_elements.mean_anomaly_at_epoch:.6f}_"
            f"{orbital_elements.epoch:.6f}_"
            f"{central_mass:.3e}_"
            f"{julian_date:.6f}"
        )
        
        # MD5ハッシュでキーを短縮
        return hashlib.md5(elements_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str, julian_date: float) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        キャッシュから結果を取得
        
        Args:
            cache_key: キャッシュキー
            julian_date: ユリウス日
            
        Returns:
            キャッシュされた結果、なければNone
        """
        if cache_key not in self.position_cache:
            return None
        
        cached_data = self.position_cache[cache_key]
        cached_result, cached_time = cached_data['result'], cached_data['time']
        
        # 時間の許容誤差内かチェック
        if abs(julian_date - cached_time) <= self.cache_time_tolerance:
            return cached_result
        
        # 時間が許容誤差外なら削除
        del self.position_cache[cache_key]
        return None
    
    def _store_in_cache(self, 
                       cache_key: str, 
                       result: Tuple[np.ndarray, np.ndarray], 
                       julian_date: float) -> None:
        """
        結果をキャッシュに保存
        
        Args:
            cache_key: キャッシュキー
            result: 計算結果
            julian_date: ユリウス日
        """
        # キャッシュサイズ制限チェック
        if len(self.position_cache) >= self.cache_max_size:
            self._evict_oldest_cache_entry()
        
        self.position_cache[cache_key] = {
            'result': result,
            'time': julian_date,
            'access_count': 1
        }
    
    def _evict_oldest_cache_entry(self) -> None:
        """
        最も古いキャッシュエントリを削除
        """
        if not self.position_cache:
            return
        
        # 最も古いエントリを探す（アクセス数が最小のもの）
        oldest_key = min(
            self.position_cache.keys(),
            key=lambda k: self.position_cache[k]['access_count']
        )
        del self.position_cache[oldest_key]
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self.position_cache.clear()
        self.cache_hit_count = 0
        self.cache_miss_count = 0
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        キャッシュ統計を取得
        
        Returns:
            キャッシュ統計の辞書
        """
        total_requests = self.cache_hit_count + self.cache_miss_count
        hit_rate = (self.cache_hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.position_cache),
            'cache_hit_count': self.cache_hit_count,
            'cache_miss_count': self.cache_miss_count,
            'cache_hit_rate_percent': hit_rate,
            'total_requests': total_requests
        }
    
    def _calculate_mean_motion(self, 
                             orbital_elements: OrbitalElements, 
                             central_mass: float) -> float:
        """
        平均運動を計算
        
        Args:
            orbital_elements: 軌道要素
            central_mass: 中心天体質量 (kg)
            
        Returns:
            平均運動 (rad/day)
        """
        a_m = orbital_elements.semi_major_axis * self.au_to_km * 1000  # AU -> m
        
        # n = sqrt(GM/a³)
        mean_motion_rad_per_sec = np.sqrt(self.gravitational_constant * central_mass / (a_m ** 3))
        
        # rad/sec -> rad/day
        return mean_motion_rad_per_sec * 86400
    
    def _solve_kepler_equation(self, mean_anomaly: float, eccentricity: float) -> float:
        """
        ケプラー方程式を数値的に解く
        
        Args:
            mean_anomaly: 平均近点角 (rad)
            eccentricity: 離心率
            
        Returns:
            離心近点角 (rad)
        """
        # 初期推定値
        E = mean_anomaly
        
        # ニュートン・ラフソン法
        for _ in range(self.max_iterations):
            f = E - eccentricity * np.sin(E) - mean_anomaly
            f_prime = 1 - eccentricity * np.cos(E)
            
            if abs(f_prime) < 1e-15:
                break
            
            delta_E = f / f_prime
            E -= delta_E
            
            if abs(delta_E) < self.convergence_tolerance:
                break
        
        return E
    
    def _calculate_true_anomaly(self, eccentric_anomaly: float, eccentricity: float) -> float:
        """
        真近点角を計算
        
        Args:
            eccentric_anomaly: 離心近点角 (rad)
            eccentricity: 離心率
            
        Returns:
            真近点角 (rad)
        """
        cos_E = np.cos(eccentric_anomaly)
        sin_E = np.sin(eccentric_anomaly)
        
        cos_nu = (cos_E - eccentricity) / (1 - eccentricity * cos_E)
        sin_nu = (np.sqrt(1 - eccentricity**2) * sin_E) / (1 - eccentricity * cos_E)
        
        return np.arctan2(sin_nu, cos_nu)
    
    def _calculate_orbital_radius(self, 
                                true_anomaly: float, 
                                orbital_elements: OrbitalElements) -> float:
        """
        軌道半径を計算
        
        Args:
            true_anomaly: 真近点角 (rad)
            orbital_elements: 軌道要素
            
        Returns:
            軌道半径 (km)
        """
        a = orbital_elements.semi_major_axis * self.au_to_km
        e = orbital_elements.eccentricity
        
        return a * (1 - e**2) / (1 + e * np.cos(true_anomaly))
    
    def _calculate_orbital_position(self, true_anomaly: float, orbital_radius: float) -> np.ndarray:
        """
        軌道面での位置を計算
        
        Args:
            true_anomaly: 真近点角 (rad)
            orbital_radius: 軌道半径 (km)
            
        Returns:
            軌道面での位置 (km)
        """
        x = orbital_radius * np.cos(true_anomaly)
        y = orbital_radius * np.sin(true_anomaly)
        
        return np.array([x, y])
    
    def _calculate_orbital_velocity(self, 
                                  true_anomaly: float,
                                  orbital_elements: OrbitalElements,
                                  central_mass: float) -> np.ndarray:
        """
        軌道面での速度を計算
        
        Args:
            true_anomaly: 真近点角 (rad)
            orbital_elements: 軌道要素
            central_mass: 中心天体質量 (kg)
            
        Returns:
            軌道面での速度 (km/s)
        """
        a = orbital_elements.semi_major_axis * self.au_to_km * 1000  # km -> m
        e = orbital_elements.eccentricity
        
        # 重力パラメータ
        mu = self.gravitational_constant * central_mass
        
        # 軌道面での速度成分
        v_magnitude = np.sqrt(mu * (2 / (a * (1 - e**2) / (1 + e * np.cos(true_anomaly))) - 1 / a))
        
        # 速度の方向
        h = np.sqrt(mu * a * (1 - e**2))  # 角運動量の大きさ
        r = a * (1 - e**2) / (1 + e * np.cos(true_anomaly))
        
        v_r = (mu / h) * e * np.sin(true_anomaly)  # 動径方向速度
        v_theta = h / r  # 接線方向速度
        
        # 軌道面での速度ベクトル
        vx = v_r * np.cos(true_anomaly) - v_theta * np.sin(true_anomaly)
        vy = v_r * np.sin(true_anomaly) + v_theta * np.cos(true_anomaly)
        
        return np.array([vx, vy]) / 1000  # m/s -> km/s
    
    def _transform_to_heliocentric(self, 
                                 orbital_position: np.ndarray, 
                                 orbital_elements: OrbitalElements) -> np.ndarray:
        """
        軌道面座標から太陽中心座標系に変換
        
        Args:
            orbital_position: 軌道面での位置 (km)
            orbital_elements: 軌道要素
            
        Returns:
            太陽中心座標系での位置 (km)
        """
        # 角度をラジアンに変換
        i = np.radians(orbital_elements.inclination)
        omega = np.radians(orbital_elements.longitude_of_ascending_node)
        w = np.radians(orbital_elements.argument_of_perihelion)
        
        # 回転行列の要素
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
    
    def _transform_velocity_to_heliocentric(self, 
                                          orbital_velocity: np.ndarray,
                                          true_anomaly: float,
                                          orbital_elements: OrbitalElements) -> np.ndarray:
        """
        軌道面速度から太陽中心座標系速度に変換
        
        Args:
            orbital_velocity: 軌道面での速度 (km/s)
            true_anomaly: 真近点角 (rad)
            orbital_elements: 軌道要素
            
        Returns:
            太陽中心座標系での速度 (km/s)
        """
        # orbital_velocityを3次元に拡張
        vx_orb, vy_orb = orbital_velocity
        vz_orb = 0.0
        
        # 軌道面座標から太陽中心座標系への変換行列を適用
        # （位置変換と同じ回転行列を使用）
        orbital_velocity_3d = np.array([vx_orb, vy_orb, vz_orb])
        return self._transform_to_heliocentric(orbital_velocity_3d[:2], orbital_elements)
    
    def calculate_orbital_elements_from_state(self, 
                                            position: np.ndarray,
                                            velocity: np.ndarray,
                                            central_mass: float = None) -> OrbitalElements:
        """
        状態ベクトル（位置・速度）から軌道要素を計算
        
        Args:
            position: 位置ベクトル (km)
            velocity: 速度ベクトル (km/s)
            central_mass: 中心天体質量 (kg)
            
        Returns:
            軌道要素
        """
        if central_mass is None:
            central_mass = self.solar_mass
        
        # 単位変換
        r = position * 1000  # km -> m
        v = velocity * 1000  # km/s -> m/s
        
        mu = self.gravitational_constant * central_mass
        
        # 距離と速度の大きさ
        r_mag = np.linalg.norm(r)
        v_mag = np.linalg.norm(v)
        
        # 角運動量ベクトル
        h_vec = np.cross(r, v)
        h_mag = np.linalg.norm(h_vec)
        
        # 離心率ベクトル
        e_vec = np.cross(v, h_vec) / mu - r / r_mag
        e_mag = np.linalg.norm(e_vec)
        
        # 軌道長半径
        a = 1 / (2 / r_mag - v_mag**2 / mu)
        
        # 軌道傾斜角
        i = np.arccos(h_vec[2] / h_mag)
        
        # 昇交点経度
        n_vec = np.cross([0, 0, 1], h_vec)
        n_mag = np.linalg.norm(n_vec)
        
        if n_mag > 0:
            omega = np.arccos(n_vec[0] / n_mag)
            if n_vec[1] < 0:
                omega = 2 * np.pi - omega
        else:
            omega = 0
        
        # 近日点引数
        if n_mag > 0 and e_mag > 0:
            w = np.arccos(np.dot(n_vec, e_vec) / (n_mag * e_mag))
            if e_vec[2] < 0:
                w = 2 * np.pi - w
        else:
            w = 0
        
        # 真近点角
        if e_mag > 0:
            nu = np.arccos(np.dot(e_vec, r) / (e_mag * r_mag))
            if np.dot(r, v) < 0:
                nu = 2 * np.pi - nu
        else:
            nu = 0
        
        # 平均近点角（簡易計算）
        E = 2 * np.arctan(np.sqrt((1 - e_mag) / (1 + e_mag)) * np.tan(nu / 2))
        M = E - e_mag * np.sin(E)
        
        return OrbitalElements(
            semi_major_axis=a / (self.au_to_km * 1000),  # m -> AU
            eccentricity=e_mag,
            inclination=np.degrees(i),
            longitude_of_ascending_node=np.degrees(omega),
            argument_of_perihelion=np.degrees(w),
            mean_anomaly_at_epoch=np.degrees(M),
            epoch=0.0  # 要設定
        )
    
    def calculate_orbital_period(self, 
                               orbital_elements: OrbitalElements,
                               central_mass: float = None) -> float:
        """
        軌道周期を計算
        
        Args:
            orbital_elements: 軌道要素
            central_mass: 中心天体質量 (kg)
            
        Returns:
            軌道周期 (日)
        """
        if central_mass is None:
            central_mass = self.solar_mass
        
        a_m = orbital_elements.semi_major_axis * self.au_to_km * 1000  # AU -> m
        mu = self.gravitational_constant * central_mass
        
        # ケプラーの第3法則 T = 2π√(a³/μ)
        period_seconds = 2 * np.pi * np.sqrt(a_m**3 / mu)
        
        return period_seconds / 86400  # 秒 -> 日
    
    def calculate_aphelion_perihelion(self, orbital_elements: OrbitalElements) -> Tuple[float, float]:
        """
        遠日点・近日点距離を計算
        
        Args:
            orbital_elements: 軌道要素
            
        Returns:
            (遠日点距離(AU), 近日点距離(AU))
        """
        a = orbital_elements.semi_major_axis
        e = orbital_elements.eccentricity
        
        aphelion = a * (1 + e)
        perihelion = a * (1 - e)
        
        return aphelion, perihelion
    
    def get_orbit_info(self, orbital_elements: OrbitalElements) -> Dict[str, float]:
        """
        軌道の詳細情報を取得
        
        Args:
            orbital_elements: 軌道要素
            
        Returns:
            軌道情報の辞書
        """
        period = self.calculate_orbital_period(orbital_elements)
        aphelion, perihelion = self.calculate_aphelion_perihelion(orbital_elements)
        
        return {
            "period_days": period,
            "period_years": period / 365.25,
            "aphelion_au": aphelion,
            "perihelion_au": perihelion,
            "semi_major_axis_au": orbital_elements.semi_major_axis,
            "eccentricity": orbital_elements.eccentricity,
            "inclination_deg": orbital_elements.inclination,
            "longitude_ascending_node_deg": orbital_elements.longitude_of_ascending_node,
            "argument_perihelion_deg": orbital_elements.argument_of_perihelion
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"OrbitCalculator (許容誤差: {self.convergence_tolerance}, 最大反復: {self.max_iterations})"