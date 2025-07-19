"""
軌道要素クラスの実装

ケプラー軌道要素を表現し、軌道計算に必要な
基本的なパラメータを管理します。
"""

import numpy as np
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class OrbitalElements:
    """
    軌道要素データクラス
    
    ケプラー軌道の6つの軌道要素を保持し、
    軌道の形状と向きを完全に定義します。
    """
    
    semi_major_axis: float          # 軌道長半径 (AU)
    eccentricity: float             # 離心率
    inclination: float              # 軌道傾斜角 (度)
    longitude_of_ascending_node: float  # 昇交点黄経 (度)
    argument_of_perihelion: float       # 近日点引数 (度)
    mean_anomaly_at_epoch: float        # 元期における平均近点角 (度)
    epoch: float                        # 元期 (ユリウス日)
    
    def __post_init__(self):
        """初期化後の検証と正規化"""
        self._validate_parameters()
        self._normalize_angles()
    
    def _validate_parameters(self) -> None:
        """軌道要素の妥当性を検証"""
        if self.semi_major_axis <= 0:
            raise ValueError("軌道長半径は正の値である必要があります")
        
        if not (0 <= self.eccentricity < 1):
            raise ValueError("離心率は0以上1未満である必要があります（楕円軌道）")
    
    def _normalize_angles(self) -> None:
        """角度を0-360度の範囲に正規化"""
        self.inclination = self._normalize_angle(self.inclination)
        self.longitude_of_ascending_node = self._normalize_angle(self.longitude_of_ascending_node)
        self.argument_of_perihelion = self._normalize_angle(self.argument_of_perihelion)
        self.mean_anomaly_at_epoch = self._normalize_angle(self.mean_anomaly_at_epoch)
    
    def _normalize_angle(self, angle: float) -> float:
        """角度を0-360度の範囲に正規化"""
        return angle % 360.0
    
    def get_orbital_period(self) -> float:
        """
        軌道周期を計算（日）
        
        ケプラーの第3法則: P² = a³ (太陽質量=1, AU単位系)
        """
        # 太陽重力パラメータ (AU³/day²)
        GM_sun = 2.959122082855911e-04
        
        # ケプラーの第3法則
        period_squared = (4 * np.pi**2 * self.semi_major_axis**3) / GM_sun
        return np.sqrt(period_squared)
    
    def get_perihelion_distance(self) -> float:
        """近日点距離を計算（AU）"""
        return self.semi_major_axis * (1 - self.eccentricity)
    
    def get_aphelion_distance(self) -> float:
        """遠日点距離を計算（AU）"""
        return self.semi_major_axis * (1 + self.eccentricity)
    
    def copy(self) -> 'OrbitalElements':
        """軌道要素のコピーを作成"""
        return OrbitalElements(
            semi_major_axis=self.semi_major_axis,
            eccentricity=self.eccentricity,
            inclination=self.inclination,
            longitude_of_ascending_node=self.longitude_of_ascending_node,
            argument_of_perihelion=self.argument_of_perihelion,
            mean_anomaly_at_epoch=self.mean_anomaly_at_epoch,
            epoch=self.epoch
        )
    
    def to_dict(self) -> Dict[str, float]:
        """辞書形式に変換"""
        return {
            'semi_major_axis': self.semi_major_axis,
            'eccentricity': self.eccentricity,
            'inclination': self.inclination,
            'longitude_of_ascending_node': self.longitude_of_ascending_node,
            'argument_of_perihelion': self.argument_of_perihelion,
            'mean_anomaly_at_epoch': self.mean_anomaly_at_epoch,
            'epoch': self.epoch
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'OrbitalElements':
        """辞書から軌道要素を作成"""
        return cls(**data)
    
    def __eq__(self, other) -> bool:
        """等価性の比較"""
        if not isinstance(other, OrbitalElements):
            return False
        
        tolerance = 1e-10
        return (
            abs(self.semi_major_axis - other.semi_major_axis) < tolerance and
            abs(self.eccentricity - other.eccentricity) < tolerance and
            abs(self.inclination - other.inclination) < tolerance and
            abs(self.longitude_of_ascending_node - other.longitude_of_ascending_node) < tolerance and
            abs(self.argument_of_perihelion - other.argument_of_perihelion) < tolerance and
            abs(self.mean_anomaly_at_epoch - other.mean_anomaly_at_epoch) < tolerance and
            abs(self.epoch - other.epoch) < tolerance
        )