"""
フラスタムカリングシステムの実装

カメラの視錐台外にあるオブジェクトを効率的に除外し、
レンダリングパフォーマンスを向上させます。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PlaneLocation(Enum):
    """平面に対する位置関係"""
    FRONT = 1    # 平面の前（内側）
    BACK = -1    # 平面の後ろ（外側）
    ON_PLANE = 0 # 平面上


@dataclass
class Plane:
    """3D平面を表すクラス"""
    normal: np.ndarray  # 法線ベクトル（正規化済み）
    distance: float     # 原点からの距離
    
    def distance_to_point(self, point: np.ndarray) -> float:
        """
        点から平面までの符号付き距離を計算
        
        Args:
            point: 3D座標点
            
        Returns:
            符号付き距離（正: 法線方向、負: 反対方向）
        """
        return np.dot(self.normal, point) + self.distance
    
    def classify_point(self, point: np.ndarray) -> PlaneLocation:
        """
        点と平面の位置関係を判定
        
        Args:
            point: 3D座標点
            
        Returns:
            位置関係
        """
        distance = self.distance_to_point(point)
        if distance > 1e-6:
            return PlaneLocation.FRONT
        elif distance < -1e-6:
            return PlaneLocation.BACK
        else:
            return PlaneLocation.ON_PLANE
    
    def is_sphere_on_front_side(self, center: np.ndarray, radius: float) -> bool:
        """
        球が平面の前側（内側）にあるかを判定
        
        Args:
            center: 球の中心座標
            radius: 球の半径
            
        Returns:
            前側にある場合True
        """
        distance = self.distance_to_point(center)
        return distance > -radius


@dataclass
class BoundingSphere:
    """バウンディングスフィア（境界球）"""
    center: np.ndarray  # 中心座標
    radius: float       # 半径
    
    def transformed(self, position: np.ndarray, scale: float = 1.0) -> 'BoundingSphere':
        """
        変換後のバウンディングスフィアを生成
        
        Args:
            position: 新しい位置
            scale: スケール倍率
            
        Returns:
            変換後のバウンディングスフィア
        """
        return BoundingSphere(
            center=self.center + position,
            radius=self.radius * scale
        )


class Frustum:
    """
    視錐台（フラスタム）を表すクラス
    
    6つの平面（近距離、遠距離、上、下、左、右）で構成される
    視錐台を管理し、オブジェクトのカリング判定を行います。
    """
    
    def __init__(self):
        """視錐台の初期化"""
        # 6つの平面（near, far, top, bottom, left, right）
        self.planes: List[Plane] = []
        
        # デバッグ情報
        self.last_update_info: Dict[str, Any] = {}
    
    def update_from_camera(self, camera_params: Dict[str, Any]) -> None:
        """
        カメラパラメータから視錐台を更新
        
        Args:
            camera_params: カメラパラメータ辞書
                - position: カメラ位置
                - center: 注視点
                - fov: 視野角（度）
                - aspect_ratio: アスペクト比
                - near: 近距離クリップ面
                - far: 遠距離クリップ面
        """
        position = np.array(camera_params['position'])
        center = np.array(camera_params['center'])
        fov = camera_params['fov']
        aspect = camera_params.get('aspect_ratio', 1.0)
        near = camera_params.get('near', 0.01)
        far = camera_params.get('far', 100.0)
        up = np.array(camera_params.get('up', [0, 0, 1]))
        
        # ビュー方向ベクトルを計算（カメラから注視点への方向）
        forward = center - position
        forward_length = np.linalg.norm(forward)
        if forward_length > 0:
            forward = forward / forward_length
        else:
            forward = np.array([0, 0, -1])
        
        # 右方向ベクトルを計算
        right = np.cross(forward, up)
        right_length = np.linalg.norm(right)
        if right_length > 0:
            right = right / right_length
        else:
            right = np.array([1, 0, 0])
        
        # 実際の上方向ベクトルを計算
        actual_up = np.cross(right, forward)
        
        # 視野角をラジアンに変換
        fov_rad = np.radians(fov)
        half_fov = fov_rad / 2.0
        
        # 近距離・遠距離平面での視錐台のサイズを計算
        near_height = 2.0 * np.tan(half_fov) * near
        near_width = near_height * aspect
        far_height = 2.0 * np.tan(half_fov) * far
        far_width = far_height * aspect
        
        # 視錐台の平面を構築
        self.planes = []
        
        # 近距離・遠距離平面の位置
        near_center = position + forward * near
        far_center = position + forward * far
        
        # 近距離平面（カメラから見て前方向の法線）
        self.planes.append(Plane(
            normal=forward,
            distance=-np.dot(forward, near_center)
        ))
        
        # 遠距離平面（カメラから見て後方向の法線）
        self.planes.append(Plane(
            normal=-forward,
            distance=np.dot(forward, far_center)
        ))
        
        # 視錐台の4つの側面を計算
        # 各平面の法線は視錐台の内側を向く必要がある
        
        # 視錐台の角を計算
        half_near_height = near_height / 2
        half_near_width = near_width / 2
        
        # 上平面: カメラから近距離面の上端へのベクトルと右ベクトルの外積
        top_edge = near_center + actual_up * half_near_height - position
        top_normal = np.cross(top_edge, right)
        if np.linalg.norm(top_normal) > 0:
            top_normal = top_normal / np.linalg.norm(top_normal)
            # 法線を内側向きに調整
            if np.dot(top_normal, position - near_center) > 0:
                top_normal = -top_normal
            self.planes.append(Plane(
                normal=top_normal,
                distance=-np.dot(top_normal, position)
            ))
        
        # 下平面: カメラから近距離面の下端へのベクトルと左ベクトルの外積
        bottom_edge = near_center - actual_up * half_near_height - position
        bottom_normal = np.cross(bottom_edge, -right)
        if np.linalg.norm(bottom_normal) > 0:
            bottom_normal = bottom_normal / np.linalg.norm(bottom_normal)
            # 法線を内側向きに調整
            if np.dot(bottom_normal, position - near_center) > 0:
                bottom_normal = -bottom_normal
            self.planes.append(Plane(
                normal=bottom_normal,
                distance=-np.dot(bottom_normal, position)
            ))
        
        # 左平面: カメラから近距離面の左端へのベクトルと上ベクトルの外積
        left_edge = near_center - right * half_near_width - position
        left_normal = np.cross(left_edge, actual_up)
        if np.linalg.norm(left_normal) > 0:
            left_normal = left_normal / np.linalg.norm(left_normal)
            # 法線を内側向きに調整
            if np.dot(left_normal, position - near_center) > 0:
                left_normal = -left_normal
            self.planes.append(Plane(
                normal=left_normal,
                distance=-np.dot(left_normal, position)
            ))
        
        # 右平面: カメラから近距離面の右端へのベクトルと下ベクトルの外積
        right_edge = near_center + right * half_near_width - position
        right_normal = np.cross(right_edge, -actual_up)
        if np.linalg.norm(right_normal) > 0:
            right_normal = right_normal / np.linalg.norm(right_normal)
            # 法線を内側向きに調整
            if np.dot(right_normal, position - near_center) > 0:
                right_normal = -right_normal
            self.planes.append(Plane(
                normal=right_normal,
                distance=-np.dot(right_normal, position)
            ))
        
        # デバッグ情報を保存
        self.last_update_info = {
            'position': position.tolist(),
            'center': center.tolist(),
            'fov': fov,
            'aspect_ratio': aspect,
            'near': near,
            'far': far
        }
    
    def is_sphere_visible(self, sphere: BoundingSphere) -> bool:
        """
        球が視錐台内に見えるかを判定
        
        Args:
            sphere: バウンディングスフィア
            
        Returns:
            見える場合True
        """
        # 全ての平面に対してチェック
        for plane in self.planes:
            if not plane.is_sphere_on_front_side(sphere.center, sphere.radius):
                # 一つでも平面の外側にある場合は見えない
                return False
        
        return True
    
    def is_point_visible(self, point: np.ndarray) -> bool:
        """
        点が視錐台内に見えるかを判定
        
        Args:
            point: 3D座標点
            
        Returns:
            見える場合True
        """
        # 全ての平面に対してチェック
        for plane in self.planes:
            if plane.classify_point(point) == PlaneLocation.BACK:
                # 一つでも平面の外側にある場合は見えない
                return False
        
        return True
    
    def cull_spheres(self, spheres: List[Tuple[str, BoundingSphere]]) -> List[str]:
        """
        複数の球に対してカリングを実行
        
        Args:
            spheres: (識別子, バウンディングスフィア)のリスト
            
        Returns:
            視錐台内に見える球の識別子リスト
        """
        visible = []
        
        for identifier, sphere in spheres:
            if self.is_sphere_visible(sphere):
                visible.append(identifier)
        
        return visible
    
    def get_culling_stats(self, total_objects: int, visible_objects: int) -> Dict[str, Any]:
        """
        カリング統計情報を取得
        
        Args:
            total_objects: 全オブジェクト数
            visible_objects: 可視オブジェクト数
            
        Returns:
            統計情報辞書
        """
        culled = total_objects - visible_objects
        cull_ratio = culled / total_objects if total_objects > 0 else 0.0
        
        return {
            'total_objects': total_objects,
            'visible_objects': visible_objects,
            'culled_objects': culled,
            'cull_ratio': cull_ratio,
            'frustum_info': self.last_update_info
        }


class FrustumCuller:
    """
    フラスタムカリング管理クラス
    
    オブジェクトのバウンディング情報を管理し、
    効率的なカリング処理を提供します。
    """
    
    def __init__(self):
        """フラスタムカラーの初期化"""
        self.frustum = Frustum()
        self.object_bounds: Dict[str, BoundingSphere] = {}
        self.enabled = True
        
        # カリング統計
        self._stats = {
            'frame_count': 0,
            'total_culled': 0,
            'total_checked': 0
        }
    
    def register_object(self, name: str, center: np.ndarray, radius: float) -> None:
        """
        オブジェクトのバウンディング情報を登録
        
        Args:
            name: オブジェクト名
            center: バウンディングスフィアの中心（ローカル座標）
            radius: バウンディングスフィアの半径
        """
        self.object_bounds[name] = BoundingSphere(
            center=np.array(center),
            radius=radius
        )
    
    def unregister_object(self, name: str) -> None:
        """
        オブジェクトの登録を解除
        
        Args:
            name: オブジェクト名
        """
        if name in self.object_bounds:
            del self.object_bounds[name]
    
    def update_frustum(self, camera_params: Dict[str, Any]) -> None:
        """
        カメラパラメータから視錐台を更新
        
        Args:
            camera_params: カメラパラメータ
        """
        self.frustum.update_from_camera(camera_params)
    
    def cull_objects(self, object_positions: Dict[str, np.ndarray]) -> List[str]:
        """
        オブジェクトのカリングを実行
        
        Args:
            object_positions: オブジェクト名と位置の辞書
            
        Returns:
            可視オブジェクトのリスト
        """
        if not self.enabled:
            # カリングが無効な場合は全て返す
            return list(object_positions.keys())
        
        visible_objects = []
        spheres_to_check = []
        
        # 各オブジェクトのワールド座標でのバウンディングスフィアを計算
        for name, position in object_positions.items():
            if name in self.object_bounds:
                local_sphere = self.object_bounds[name]
                world_sphere = local_sphere.transformed(position)
                spheres_to_check.append((name, world_sphere))
        
        # カリング実行
        visible_objects = self.frustum.cull_spheres(spheres_to_check)
        
        # 統計更新
        self._stats['frame_count'] += 1
        self._stats['total_checked'] += len(spheres_to_check)
        self._stats['total_culled'] += len(spheres_to_check) - len(visible_objects)
        
        return visible_objects
    
    def set_enabled(self, enabled: bool) -> None:
        """
        カリングの有効/無効を設定
        
        Args:
            enabled: 有効にする場合True
        """
        self.enabled = enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """
        カリング統計情報を取得
        
        Returns:
            統計情報辞書
        """
        avg_cull_ratio = 0.0
        if self._stats['total_checked'] > 0:
            avg_cull_ratio = self._stats['total_culled'] / self._stats['total_checked']
        
        return {
            'enabled': self.enabled,
            'frame_count': self._stats['frame_count'],
            'total_culled': self._stats['total_culled'],
            'total_checked': self._stats['total_checked'],
            'average_cull_ratio': avg_cull_ratio,
            'registered_objects': len(self.object_bounds)
        }
    
    def reset_stats(self) -> None:
        """統計情報をリセット"""
        self._stats = {
            'frame_count': 0,
            'total_culled': 0,
            'total_checked': 0
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        stats = self.get_stats()
        return (f"FrustumCuller (有効: {self.enabled}, "
                f"登録オブジェクト: {stats['registered_objects']}, "
                f"平均カリング率: {stats['average_cull_ratio']:.1%})")