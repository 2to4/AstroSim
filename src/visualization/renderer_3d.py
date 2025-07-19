"""
3Dレンダラークラスの実装

Vispyを使用した3Dシーンのレンダリング、
惑星の描画、カメラ制御などを行います。
"""

import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from vispy import scene, color
from vispy.visuals.transforms import STTransform

from ..domain.planet import Planet
from ..domain.sun import Sun
from ..domain.celestial_body import CelestialBody


class Renderer3D:
    """
    3Dシーンのレンダリングを管理するクラス
    
    Vispyを使用して太陽系の3D可視化を行います。
    惑星の描画、軌道表示、カメラ制御などを提供します。
    """
    
    def __init__(self, canvas: scene.SceneCanvas):
        """
        3Dレンダラーの初期化
        
        Args:
            canvas: Vispyのシーンキャンバス
        """
        self.canvas = canvas
        self.view = canvas.central_widget.add_view()
        
        # シーン設定
        self._setup_camera()
        self._setup_lighting()
        
        # レンダリング要素
        self.planet_visuals: Dict[str, Dict[str, Any]] = {}
        self.orbit_visuals: Dict[str, scene.visuals.Line] = {}
        self.sun_visual: Optional[scene.visuals.Sphere] = None
        
        # 表示設定
        self.show_orbits = True
        self.show_labels = True
        self.scale_factor = 1.0
        self.planet_scale = 1000.0  # 惑星サイズの拡大倍率
        
        # 座標変換（km -> 描画単位）
        self.distance_scale = 1.0 / 149597870.7  # km -> AU
        
        # 選択状態
        self.selected_planet: Optional[str] = None
        
        # 背景設定
        self.canvas.bgcolor = (0.05, 0.05, 0.1, 1.0)  # 暗い宇宙背景
    
    def _setup_camera(self) -> None:
        """カメラの初期設定"""
        self.camera = scene.TurntableCamera(
            elevation=30,
            azimuth=30,
            fov=60,
            distance=5.0,  # 5AU相当
            up='z'
        )
        self.view.camera = self.camera
    
    def _setup_lighting(self) -> None:
        """ライティングの設定"""
        # 環境光（弱い）
        self.ambient_light = scene.visuals.AmbientLight(
            color=(0.3, 0.3, 0.4, 1.0)
        )
        
        # 太陽からの指向性ライト
        self.directional_light = scene.visuals.DirectionalLight(
            color=(1.0, 1.0, 0.9, 1.0),
            direction=(0, 0, -1)
        )
    
    def add_sun(self, sun: Sun) -> None:
        """
        太陽をシーンに追加
        
        Args:
            sun: 太陽オブジェクト
        """
        # 太陽の半径をスケール（実際の太陽は小さすぎるため拡大）
        sun_radius = max(0.005, sun.radius * self.planet_scale * self.distance_scale)
        
        # 太陽の色（温度に基づく）
        visual_props = sun.get_visual_properties()
        sun_color = visual_props['color']
        
        # 太陽の球体を作成
        self.sun_visual = scene.visuals.Sphere(
            radius=sun_radius,
            color=sun_color,
            parent=self.view.scene
        )
        
        # 太陽は原点に配置
        self.sun_visual.transform = STTransform(translate=(0, 0, 0))
        
        # 太陽の発光効果（簡易実装）
        self.sun_visual.shading = 'flat'
    
    def add_planet(self, planet: Planet) -> None:
        """
        惑星をシーンに追加
        
        Args:
            planet: 惑星オブジェクト
        """
        planet_name = planet.name
        
        # 惑星の半径をスケール
        planet_radius = max(0.002, planet.radius * self.planet_scale * self.distance_scale)
        
        # 惑星の視覚プロパティを取得
        visual_props = planet.get_visual_properties()
        planet_color = visual_props['color']
        
        # 惑星の球体を作成
        planet_sphere = scene.visuals.Sphere(
            radius=planet_radius,
            color=planet_color,
            parent=self.view.scene
        )
        
        # ラベルを作成
        label = scene.visuals.Text(
            planet_name,
            color=(1, 1, 1, 0.8),
            font_size=12,
            parent=self.view.scene
        )
        
        # 惑星の軌道線を作成
        orbit_line = self._create_orbit_line(planet)
        
        # 惑星の視覚要素を保存
        self.planet_visuals[planet_name] = {
            'sphere': planet_sphere,
            'label': label,
            'orbit': orbit_line,
            'planet': planet
        }
    
    def _create_orbit_line(self, planet: Planet) -> scene.visuals.Line:
        """
        惑星の軌道線を作成
        
        Args:
            planet: 惑星オブジェクト
            
        Returns:
            軌道線の視覚要素
        """
        # 軌道要素から軌道線の点を計算
        orbital_elements = planet.orbital_elements
        points = []
        
        # 360度を細分化して軌道線を描画
        for angle in np.linspace(0, 2 * np.pi, 360):
            # 簡易的な楕円軌道計算
            a = orbital_elements.semi_major_axis
            e = orbital_elements.eccentricity
            
            # 極座標での半径
            r = a * (1 - e**2) / (1 + e * np.cos(angle))
            
            # 軌道面での位置
            x_orbit = r * np.cos(angle)
            y_orbit = r * np.sin(angle)
            
            # 3次元座標に変換（簡易版）
            i = np.radians(orbital_elements.inclination)
            omega = np.radians(orbital_elements.longitude_of_ascending_node)
            w = np.radians(orbital_elements.argument_of_perihelion)
            
            # 回転行列による変換
            cos_omega = np.cos(omega)
            sin_omega = np.sin(omega)
            cos_i = np.cos(i)
            sin_i = np.sin(i)
            cos_w = np.cos(w)
            sin_w = np.sin(w)
            
            x = (cos_omega * cos_w - sin_omega * sin_w * cos_i) * x_orbit + \
                (-cos_omega * sin_w - sin_omega * cos_w * cos_i) * y_orbit
            y = (sin_omega * cos_w + cos_omega * sin_w * cos_i) * x_orbit + \
                (-sin_omega * sin_w + cos_omega * cos_w * cos_i) * y_orbit
            z = sin_w * sin_i * x_orbit + cos_w * sin_i * y_orbit
            
            # スケール調整
            points.append([x * self.distance_scale, y * self.distance_scale, z * self.distance_scale])
        
        # 軌道線を作成
        orbit_line = scene.visuals.Line(
            pos=np.array(points),
            color=(0.5, 0.5, 0.5, 0.3),
            width=1.0,
            parent=self.view.scene
        )
        
        return orbit_line
    
    def update_planet_position(self, planet_name: str, position: np.ndarray) -> None:
        """
        惑星の位置を更新
        
        Args:
            planet_name: 惑星名
            position: 新しい位置 (km)
        """
        if planet_name not in self.planet_visuals:
            return
        
        visual_data = self.planet_visuals[planet_name]
        
        # 位置をスケール変換
        scaled_position = position * self.distance_scale
        
        # 球体の位置を更新
        sphere = visual_data['sphere']
        sphere.transform = STTransform(translate=scaled_position)
        
        # ラベルの位置を更新（惑星の少し上に配置）
        label = visual_data['label']
        label_offset = np.array([0, 0, 0.1])  # 少し上にオフセット
        label.transform = STTransform(translate=scaled_position + label_offset)
    
    def update_planet_rotation(self, planet_name: str, rotation_angle: float) -> None:
        """
        惑星の自転角度を更新
        
        Args:
            planet_name: 惑星名
            rotation_angle: 回転角度 (度)
        """
        if planet_name not in self.planet_visuals:
            return
        
        visual_data = self.planet_visuals[planet_name]
        sphere = visual_data['sphere']
        
        # 現在の位置を保持して回転を適用
        current_transform = sphere.transform
        if hasattr(current_transform, 'translate'):
            position = current_transform.translate
        else:
            position = (0, 0, 0)
        
        # 回転と平行移動を組み合わせた変換
        sphere.transform = STTransform(
            translate=position,
            rotate=(rotation_angle, 0, 0, 1)  # Z軸周りの回転
        )
    
    def set_planet_selected(self, planet_name: Optional[str]) -> None:
        """
        惑星の選択状態を設定
        
        Args:
            planet_name: 選択する惑星名（Noneで選択解除）
        """
        # 前回の選択を解除
        if self.selected_planet and self.selected_planet in self.planet_visuals:
            old_visual = self.planet_visuals[self.selected_planet]
            old_sphere = old_visual['sphere']
            # 元の色に戻す
            planet = old_visual['planet']
            visual_props = planet.get_visual_properties()
            old_sphere.color = visual_props['color']
        
        # 新しい選択を適用
        self.selected_planet = planet_name
        if planet_name and planet_name in self.planet_visuals:
            visual_data = self.planet_visuals[planet_name]
            sphere = visual_data['sphere']
            # 選択状態を示すために明るくする
            sphere.color = (1.0, 1.0, 0.0, 1.0)  # 黄色でハイライト
    
    def set_orbit_visibility(self, visible: bool) -> None:
        """
        軌道線の表示/非表示を設定
        
        Args:
            visible: 表示するかどうか
        """
        self.show_orbits = visible
        
        for visual_data in self.planet_visuals.values():
            orbit = visual_data['orbit']
            orbit.visible = visible
    
    def set_label_visibility(self, visible: bool) -> None:
        """
        ラベルの表示/非表示を設定
        
        Args:
            visible: 表示するかどうか
        """
        self.show_labels = visible
        
        for visual_data in self.planet_visuals.values():
            label = visual_data['label']
            label.visible = visible
    
    def set_scale_factor(self, factor: float) -> None:
        """
        表示スケールを設定
        
        Args:
            factor: スケール倍率
        """
        self.scale_factor = factor
        
        # 全ての惑星の位置を再計算
        for planet_name, visual_data in self.planet_visuals.items():
            planet = visual_data['planet']
            scaled_position = planet.position * self.distance_scale * factor
            
            sphere = visual_data['sphere']
            sphere.transform = STTransform(translate=scaled_position)
            
            label = visual_data['label']
            label_offset = np.array([0, 0, 0.1])
            label.transform = STTransform(translate=scaled_position + label_offset)
    
    def focus_on_planet(self, planet_name: str, distance: float = 2.0) -> None:
        """
        特定の惑星にフォーカス
        
        Args:
            planet_name: フォーカスする惑星名
            distance: カメラからの距離
        """
        if planet_name not in self.planet_visuals:
            return
        
        visual_data = self.planet_visuals[planet_name]
        planet = visual_data['planet']
        
        # 惑星の位置を取得
        planet_position = planet.position * self.distance_scale
        
        # カメラを惑星にフォーカス
        self.camera.center = planet_position
        self.camera.distance = distance
    
    def reset_view(self) -> None:
        """カメラビューをリセット"""
        self.camera.center = (0, 0, 0)
        self.camera.distance = 5.0
        self.camera.elevation = 30
        self.camera.azimuth = 30
    
    def pick_object(self, x: int, y: int) -> Optional[str]:
        """
        画面座標から3Dオブジェクトを選択
        
        Args:
            x: 画面X座標
            y: 画面Y座標
            
        Returns:
            選択されたオブジェクト名（惑星名）
        """
        # 簡易的なピッキング実装
        # 実際の実装では、レイキャスティングを使用
        
        # 現在は最も近い惑星を返す簡易版
        canvas_coords = np.array([x, y])
        
        min_distance = float('inf')
        selected_planet = None
        
        for planet_name, visual_data in self.planet_visuals.items():
            planet = visual_data['planet']
            planet_position = planet.position * self.distance_scale
            
            # 3D座標を2D画面座標に変換（簡易版）
            # 実際の実装では、カメラの変換行列を使用
            screen_pos = np.array([planet_position[0], planet_position[1]])
            
            distance = np.linalg.norm(canvas_coords - screen_pos * 100)  # 適当なスケール
            
            if distance < min_distance and distance < 50:  # 50ピクセル以内
                min_distance = distance
                selected_planet = planet_name
        
        return selected_planet
    
    def render(self) -> None:
        """シーンをレンダリング"""
        # Vispyは自動的にレンダリングを行うため、
        # 特別な処理は必要ない
        pass
    
    def get_render_info(self) -> Dict[str, Any]:
        """
        レンダリング情報を取得
        
        Returns:
            レンダリング状態の辞書
        """
        return {
            'planet_count': len(self.planet_visuals),
            'show_orbits': self.show_orbits,
            'show_labels': self.show_labels,
            'scale_factor': self.scale_factor,
            'selected_planet': self.selected_planet,
            'camera_distance': self.camera.distance,
            'camera_center': self.camera.center
        }
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        # 全ての視覚要素を削除
        for visual_data in self.planet_visuals.values():
            if visual_data['sphere'].parent:
                visual_data['sphere'].parent = None
            if visual_data['label'].parent:
                visual_data['label'].parent = None
            if visual_data['orbit'].parent:
                visual_data['orbit'].parent = None
        
        if self.sun_visual and self.sun_visual.parent:
            self.sun_visual.parent = None
        
        self.planet_visuals.clear()
        self.sun_visual = None
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"Renderer3D ({len(self.planet_visuals)}惑星, 軌道表示: {self.show_orbits})"