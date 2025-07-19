"""
カメラコントローラークラスの実装

3Dシーンのカメラ制御、視点変更、
フォーカス機能などを提供します。
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from vispy import scene
from vispy.util.quaternion import Quaternion


class CameraController:
    """
    3Dカメラの制御クラス
    
    カメラの回転、ズーム、パン、フォーカス機能を提供し、
    ユーザーの操作に応じて視点を制御します。
    """
    
    def __init__(self, view: scene.ViewBox):
        """
        カメラコントローラーの初期化
        
        Args:
            view: Vispyのビューボックス
        """
        self.view = view
        
        # Turntableカメラを設定
        self.camera = scene.TurntableCamera(
            elevation=30.0,
            azimuth=30.0,
            fov=60.0,
            distance=5.0,  # 5AU相当
            up='z'
        )
        self.view.camera = self.camera
        
        # カメラの制限設定
        self.min_distance = 0.1    # 最小距離（AU）
        self.max_distance = 50.0   # 最大距離（AU）
        self.min_elevation = -89.0 # 最小仰角
        self.max_elevation = 89.0  # 最大仰角
        
        # 操作感度設定
        self.rotation_sensitivity = 1.0
        self.zoom_sensitivity = 1.1
        self.pan_sensitivity = 0.01
        
        # 初期位置を保存
        self.default_distance = 5.0
        self.default_elevation = 30.0
        self.default_azimuth = 30.0
        self.default_center = np.array([0.0, 0.0, 0.0])
        
        # アニメーション用
        self.animation_steps = 30
        self.is_animating = False
        
        # フォーカス追跡
        self.tracking_target: Optional[str] = None
        self.tracking_offset = np.array([0.0, 0.0, 0.0])
    
    def rotate(self, delta_azimuth: float, delta_elevation: float) -> None:
        """
        カメラを回転
        
        Args:
            delta_azimuth: 方位角の変化量（度）
            delta_elevation: 仰角の変化量（度）
        """
        if self.is_animating:
            return
        
        # 感度を適用
        delta_azimuth *= self.rotation_sensitivity
        delta_elevation *= self.rotation_sensitivity
        
        # 新しい角度を計算
        new_azimuth = self.camera.azimuth + delta_azimuth
        new_elevation = self.camera.elevation + delta_elevation
        
        # 仰角の制限を適用
        new_elevation = np.clip(new_elevation, self.min_elevation, self.max_elevation)
        
        # 方位角を0-360度の範囲に正規化
        new_azimuth = new_azimuth % 360.0
        
        # カメラに適用
        self.camera.azimuth = new_azimuth
        self.camera.elevation = new_elevation
    
    def zoom(self, factor: float) -> None:
        """
        ズームイン/アウト
        
        Args:
            factor: ズーム倍率（>1でズームイン、<1でズームアウト）
        """
        if self.is_animating:
            return
        
        # 現在の距離を取得
        current_distance = self.camera.distance
        
        # 新しい距離を計算
        if factor > 1:
            new_distance = current_distance / self.zoom_sensitivity
        else:
            new_distance = current_distance * self.zoom_sensitivity
        
        # 距離の制限を適用
        new_distance = np.clip(new_distance, self.min_distance, self.max_distance)
        
        # カメラに適用
        self.camera.distance = new_distance
    
    def pan(self, delta_x: float, delta_y: float) -> None:
        """
        カメラを平行移動
        
        Args:
            delta_x: X方向の移動量
            delta_y: Y方向の移動量
        """
        if self.is_animating:
            return
        
        # カメラの向きに基づいて移動方向を計算
        azimuth_rad = np.radians(self.camera.azimuth)
        elevation_rad = np.radians(self.camera.elevation)
        
        # パン感度を距離に応じて調整
        sensitivity = self.pan_sensitivity * self.camera.distance
        
        # 右方向ベクトル
        right_vector = np.array([
            np.cos(azimuth_rad + np.pi/2),
            np.sin(azimuth_rad + np.pi/2),
            0
        ])
        
        # 上方向ベクトル（カメラの仰角を考慮）
        up_vector = np.array([
            -np.sin(azimuth_rad) * np.sin(elevation_rad),
            np.cos(azimuth_rad) * np.sin(elevation_rad),
            np.cos(elevation_rad)
        ])
        
        # 移動ベクトルを計算
        movement = (right_vector * delta_x + up_vector * delta_y) * sensitivity
        
        # 現在の中心点を移動
        current_center = np.array(self.camera.center)
        new_center = current_center + movement
        
        self.camera.center = new_center
    
    def focus_on_position(self, position: np.ndarray, distance: Optional[float] = None) -> None:
        """
        特定の位置にフォーカス
        
        Args:
            position: フォーカス位置
            distance: カメラからの距離（Noneの場合は現在の距離を維持）
        """
        if distance is None:
            distance = self.camera.distance
        
        # 距離の制限を適用
        distance = np.clip(distance, self.min_distance, self.max_distance)
        
        # アニメーション付きでフォーカス
        self._animate_to_position(position, distance)
    
    def focus_on_planet(self, planet_position: np.ndarray, planet_radius: float) -> None:
        """
        惑星にフォーカス
        
        Args:
            planet_position: 惑星の位置
            planet_radius: 惑星の半径（表示スケール調整用）
        """
        # 惑星サイズに応じて適切な距離を計算
        # 惑星の半径の5-10倍程度の距離に設定
        optimal_distance = max(0.5, planet_radius * 8)
        optimal_distance = np.clip(optimal_distance, self.min_distance, self.max_distance)
        
        self.focus_on_position(planet_position, optimal_distance)
    
    def track_target(self, target_name: str, target_position: np.ndarray) -> None:
        """
        ターゲットを追跡
        
        Args:
            target_name: 追跡するターゲット名
            target_position: ターゲットの位置
        """
        self.tracking_target = target_name
        
        # 追跡オフセットを計算（現在の中心からターゲットへの相対位置）
        current_center = np.array(self.camera.center)
        self.tracking_offset = current_center - target_position
        
        # カメラの中心を更新
        self.camera.center = target_position + self.tracking_offset
    
    def update_tracking(self, target_position: np.ndarray) -> None:
        """
        追跡中のターゲット位置を更新
        
        Args:
            target_position: 新しいターゲット位置
        """
        if self.tracking_target is None:
            return
        
        # カメラの中心を新しいターゲット位置に追従
        self.camera.center = target_position + self.tracking_offset
    
    def stop_tracking(self) -> None:
        """追跡を停止"""
        self.tracking_target = None
        self.tracking_offset = np.array([0.0, 0.0, 0.0])
    
    def reset_view(self) -> None:
        """カメラビューを初期位置にリセット"""
        self._animate_to_state(
            center=self.default_center,
            distance=self.default_distance,
            elevation=self.default_elevation,
            azimuth=self.default_azimuth
        )
        self.stop_tracking()
    
    def set_view_preset(self, preset: str) -> None:
        """
        プリセットビューを設定
        
        Args:
            preset: プリセット名 ("top", "side", "front", "perspective")
        """
        presets = {
            "top": {"elevation": 90.0, "azimuth": 0.0, "distance": 8.0},
            "side": {"elevation": 0.0, "azimuth": 90.0, "distance": 8.0},
            "front": {"elevation": 0.0, "azimuth": 0.0, "distance": 8.0},
            "perspective": {"elevation": 30.0, "azimuth": 45.0, "distance": 5.0}
        }
        
        if preset in presets:
            settings = presets[preset]
            self._animate_to_state(
                center=np.array([0.0, 0.0, 0.0]),
                distance=settings["distance"],
                elevation=settings["elevation"],
                azimuth=settings["azimuth"]
            )
    
    def _animate_to_position(self, target_center: np.ndarray, target_distance: float) -> None:
        """
        指定位置へのアニメーション
        
        Args:
            target_center: 目標中心位置
            target_distance: 目標距離
        """
        self._animate_to_state(
            center=target_center,
            distance=target_distance,
            elevation=self.camera.elevation,
            azimuth=self.camera.azimuth
        )
    
    def _animate_to_state(self, center: np.ndarray, distance: float, 
                         elevation: float, azimuth: float) -> None:
        """
        指定状態へのアニメーション
        
        Args:
            center: 目標中心位置
            distance: 目標距離
            elevation: 目標仰角
            azimuth: 目標方位角
        """
        # 簡易実装：即座に移動（実際のアニメーションは複雑になるため）
        self.camera.center = center
        self.camera.distance = distance
        self.camera.elevation = elevation
        self.camera.azimuth = azimuth
    
    def update_tracking_position(self, target_position: np.ndarray) -> None:
        """
        追跡位置の更新（SceneManagerから呼び出し）
        
        Args:
            target_position: 新しいターゲット位置
        """
        self.update_tracking(target_position)
    
    def handle_mouse_press(self, event) -> bool:
        """
        マウスプレスイベントの処理
        
        Args:
            event: マウスイベント
            
        Returns:
            イベントが処理されたかどうか
        """
        # 左クリック: 回転操作の開始準備
        if event.button == 1:  # 左ボタン
            self._mouse_press_pos = event.pos
            return True
        
        # 右クリック: パン操作の開始準備
        elif event.button == 2:  # 右ボタン
            self._mouse_press_pos = event.pos
            return True
        
        return False
    
    def handle_mouse_move(self, event) -> bool:
        """
        マウス移動イベントの処理
        
        Args:
            event: マウスイベント
            
        Returns:
            イベントが処理されたかどうか
        """
        if not hasattr(self, '_mouse_press_pos'):
            return False
        
        # マウスの移動量を計算
        if hasattr(event, 'last_event') and event.last_event:
            dx = event.pos[0] - event.last_event.pos[0]
            dy = event.pos[1] - event.last_event.pos[1]
            
            # 左ドラッグ: カメラ回転
            if event.button == 1:
                # マウス移動量をカメラ回転に変換
                delta_azimuth = -dx * 0.5  # 水平移動 → 方位角
                delta_elevation = dy * 0.5  # 垂直移動 → 仰角
                self.rotate(delta_azimuth, delta_elevation)
                return True
            
            # 右ドラッグ: カメラパン
            elif event.button == 2:
                # マウス移動量をパンに変換
                pan_x = -dx * self.pan_sensitivity * self.camera.distance
                pan_y = dy * self.pan_sensitivity * self.camera.distance
                self.pan(pan_x, pan_y)
                return True
        
        return False
    
    def handle_mouse_wheel(self, event) -> bool:
        """
        マウスホイールイベントの処理
        
        Args:
            event: マウスホイールイベント
            
        Returns:
            イベントが処理されたかどうか
        """
        if hasattr(event, 'delta'):
            # ホイール方向に応じてズーム
            zoom_factor = self.zoom_sensitivity if event.delta[1] > 0 else 1.0 / self.zoom_sensitivity
            self.zoom(zoom_factor)
            return True
        
        return False
    
    def handle_key_press(self, event) -> bool:
        """
        キープレスイベントの処理
        
        Args:
            event: キーイベント
            
        Returns:
            イベントが処理されたかどうか
        """
        # キーボードショートカット
        key = event.key.name if hasattr(event.key, 'name') else str(event.key)
        
        if key == 'r' or key == 'R':
            # Rキー: ビューリセット
            self.reset_view()
            return True
        
        elif key in ['1', '2', '3', '4']:
            # 数字キー: プリセットビュー
            presets = ['top', 'side', 'front', 'perspective']
            preset_index = int(key) - 1
            if 0 <= preset_index < len(presets):
                self.set_view_preset(presets[preset_index])
                return True
        
        elif key == 'Escape':
            # Escapeキー: 追跡停止
            self.stop_tracking()
            return True
        
        return False
    
    def get_view_matrix(self) -> np.ndarray:
        """
        現在のビュー行列を取得
        
        Returns:
            4x4ビュー行列
        """
        # カメラの変換行列を取得
        return self.camera.get_state()['transform'].matrix
    
    def world_to_screen(self, world_pos: np.ndarray) -> Tuple[float, float]:
        """
        ワールド座標を画面座標に変換
        
        Args:
            world_pos: ワールド座標
            
        Returns:
            画面座標 (x, y)
        """
        # 簡易実装（正確な変換には射影行列も必要）
        view_matrix = self.get_view_matrix()
        
        # 同次座標に変換
        world_pos_homogeneous = np.append(world_pos, 1.0)
        
        # ビュー変換を適用
        view_pos = view_matrix @ world_pos_homogeneous
        
        # 画面座標への変換（簡易版）
        screen_x = view_pos[0] / view_pos[3] if view_pos[3] != 0 else 0
        screen_y = view_pos[1] / view_pos[3] if view_pos[3] != 0 else 0
        
        return (screen_x, screen_y)
    
    def screen_to_world_ray(self, screen_x: float, screen_y: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        画面座標からワールド座標へのレイを計算
        
        Args:
            screen_x: 画面X座標
            screen_y: 画面Y座標
            
        Returns:
            (レイの開始点, レイの方向)
        """
        # カメラの位置を計算
        camera_pos = self._calculate_camera_position()
        
        # 画面座標をワールド座標に変換（簡易版）
        # 実際の実装では逆射影変換が必要
        ray_direction = np.array([screen_x, screen_y, -1.0])
        ray_direction = ray_direction / np.linalg.norm(ray_direction)
        
        return camera_pos, ray_direction
    
    def _calculate_camera_position(self) -> np.ndarray:
        """
        カメラのワールド座標位置を計算
        
        Returns:
            カメラの位置
        """
        center = np.array(self.camera.center)
        distance = self.camera.distance
        elevation_rad = np.radians(self.camera.elevation)
        azimuth_rad = np.radians(self.camera.azimuth)
        
        # 球面座標からカメラ位置を計算
        camera_x = center[0] + distance * np.cos(elevation_rad) * np.cos(azimuth_rad)
        camera_y = center[1] + distance * np.cos(elevation_rad) * np.sin(azimuth_rad)
        camera_z = center[2] + distance * np.sin(elevation_rad)
        
        return np.array([camera_x, camera_y, camera_z])
    
    def set_sensitivity(self, rotation: float, zoom: float, pan: float) -> None:
        """
        操作感度を設定
        
        Args:
            rotation: 回転感度
            zoom: ズーム感度
            pan: パン感度
        """
        self.rotation_sensitivity = max(0.1, rotation)
        self.zoom_sensitivity = max(1.01, zoom)
        self.pan_sensitivity = max(0.001, pan)
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        カメラの詳細情報を取得
        
        Returns:
            カメラ状態の辞書
        """
        return {
            "center": list(self.camera.center),
            "distance": self.camera.distance,
            "elevation": self.camera.elevation,
            "azimuth": self.camera.azimuth,
            "fov": self.camera.fov,
            "tracking_target": self.tracking_target,
            "position": list(self._calculate_camera_position()),
            "up_vector": list(self.camera.up)
        }
    
    def save_view_state(self) -> Dict[str, Any]:
        """
        現在のビュー状態を保存
        
        Returns:
            ビュー状態の辞書
        """
        return {
            "center": list(self.camera.center),
            "distance": self.camera.distance,
            "elevation": self.camera.elevation,
            "azimuth": self.camera.azimuth,
            "tracking_target": self.tracking_target,
            "tracking_offset": list(self.tracking_offset)
        }
    
    def restore_view_state(self, state: Dict[str, Any]) -> None:
        """
        ビュー状態を復元
        
        Args:
            state: 保存されたビュー状態
        """
        self.camera.center = state.get("center", [0, 0, 0])
        self.camera.distance = state.get("distance", 5.0)
        self.camera.elevation = state.get("elevation", 30.0)
        self.camera.azimuth = state.get("azimuth", 30.0)
        self.tracking_target = state.get("tracking_target")
        self.tracking_offset = np.array(state.get("tracking_offset", [0, 0, 0]))
    
    def __str__(self) -> str:
        """文字列表現"""
        return (f"CameraController (距離: {self.camera.distance:.2f}, "
                f"仰角: {self.camera.elevation:.1f}°, "
                f"方位角: {self.camera.azimuth:.1f}°)")