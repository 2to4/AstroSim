"""
3Dレンダラークラスの実装

Vispyを使用した3Dシーンのレンダリング、
惑星の描画、カメラ制御などを行います。
"""

import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from vispy import scene, color
from vispy.visuals.transforms import STTransform

from src.domain.planet import Planet
from src.domain.sun import Sun
from src.domain.celestial_body import CelestialBody


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
        self.show_axes = False
        self.scale_factor = 1.0
        self.planet_scale = 200.0  # 惑星サイズの拡大倍率（太陽系全体表示用）
        
        # 座標変換（km -> 描画単位）
        self.distance_scale = 1.0 / 149597870.7  # km -> AU
        
        # 選択状態
        self.selected_planet: Optional[str] = None
        
        # レベルオブディテール（LOD）設定
        self.lod_enabled = True
        self.lod_distance_thresholds = {
            'high': 2.0,    # 2AU以内: 高詳細
            'medium': 10.0, # 10AU以内: 中詳細
            'low': 50.0     # 50AU以内: 低詳細
        }
        self.lod_sphere_subdivisions = {
            'high': 32,     # 高詳細: 32分割
            'medium': 16,   # 中詳細: 16分割
            'low': 8        # 低詳細: 8分割
        }
        
        # 背景設定（黒い宇宙）
        self.canvas.bgcolor = (0.0, 0.0, 0.0, 1.0)
        
        # 座標軸を追加
        self._setup_axes()
    
    def _setup_camera(self) -> None:
        """カメラの初期設定"""
        self.camera = scene.TurntableCamera(
            elevation=30,
            azimuth=30,
            fov=60,
            distance=80.0,  # 外惑星も含めた太陽系全体が見える距離
            up='z'
        )
        self.view.camera = self.camera
    
    def _setup_lighting(self) -> None:
        """ライティングの設定"""
        # Vispy 0.15+ではライティングAPIが変更されているため、
        # 基本的な設定のみ行う
        try:
            # 環境光の設定（利用可能な場合）
            if hasattr(scene.visuals, 'AmbientLight'):
                self.ambient_light = scene.visuals.AmbientLight(
                    color=(0.3, 0.3, 0.4, 1.0)
                )
            else:
                self.ambient_light = None
            
            # 指向性ライトの設定（利用可能な場合）
            if hasattr(scene.visuals, 'DirectionalLight'):
                self.directional_light = scene.visuals.DirectionalLight(
                    color=(1.0, 1.0, 0.9, 1.0),
                    direction=(0, 0, -1)
                )
            else:
                self.directional_light = None
        except Exception:
            # ライティングが利用できない場合はスキップ
            self.ambient_light = None
            self.directional_light = None
    
    def _setup_axes(self) -> None:
        """座標軸の設定"""
        # XYZAxisを使用（スケールを大きく）
        self.axis = scene.visuals.XYZAxis(parent=self.view.scene, width=3)
        self.axis.transform = STTransform(scale=(10, 10, 10))  # 太陽系全体表示に合わせる
        self.axis.visible = self.show_axes  # 初期表示状態を設定
    
    def add_sun(self, sun: Sun) -> None:
        """
        太陽をシーンに追加
        
        Args:
            sun: 太陽オブジェクト
        """
        # 太陽の半径をスケール（km -> AU、実際の太陽は小さすぎるため拡大）
        sun_radius_au = sun.radius / 149597870.7  # km to AU
        sun_radius = max(0.1, sun_radius_au * self.planet_scale)  # 太陽系全体表示用サイズ
        
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
        try:
            self.sun_visual.shading = 'flat'
        except AttributeError:
            # Vispy 0.15+では shading 属性が利用できない場合がある
            pass
    
    def add_planet(self, planet: Planet) -> None:
        """
        惑星をシーンに追加
        
        Args:
            planet: 惑星オブジェクト
        """
        planet_name = planet.name
        
        # 惑星の半径をスケール（km -> AU、さらに表示用に拡大）
        planet_radius_au = planet.radius / 149597870.7  # km to AU
        planet_radius = max(0.5, planet_radius_au * self.planet_scale)  # 80AU距離から見えるサイズ
        
        # 惑星の視覚プロパティを取得
        visual_props = planet.get_visual_properties()
        planet_color = visual_props['color']
        
        # 惑星の初期位置でLODレベルを決定
        # planet.positionはkm単位なので、AUに変換
        planet_position_au = planet.position / 149597870.7
        distance_to_camera = self._get_distance_to_camera(planet_position_au)
        lod_level = self._determine_lod_level(distance_to_camera)
        
        # LODレベルに応じた惑星の球体を作成
        planet_sphere = self._create_planet_sphere_with_lod(
            planet_radius, planet_color, lod_level
        )
        
        # ラベルを作成（より大きく、明るく）
        label = scene.visuals.Text(
            planet_name,
            color=(1, 1, 1, 1.0),  # 完全に不透明
            font_size=16,  # より大きなフォント
            parent=self.view.scene
        )
        
        # 惑星の軌道線を作成
        orbit_line = self._create_orbit_line(planet)
        
        # 軌道線の初期表示状態を設定
        orbit_line.visible = self.show_orbits
        
        # 惑星の初期位置を設定
        planet_sphere.transform = STTransform(translate=planet_position_au)
        label.pos = planet_position_au + np.array([0, 0, planet_radius * 2.0])  # ラベルを少し上に
        
        # 惑星の視覚要素を保存
        self.planet_visuals[planet_name] = {
            'sphere': planet_sphere,
            'label': label,
            'orbit': orbit_line,
            'planet': planet,
            'lod_level': lod_level,
            'base_radius': planet_radius,
            'base_color': planet_color
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
            
            # スケール調整（km -> AU）
            points.append([x / 149597870.7, y / 149597870.7, z / 149597870.7])
        
        # 軌道線を作成
        orbit_line = scene.visuals.Line(
            pos=np.array(points),
            color=(0.6, 0.9, 1.0, 1.0),  # 明るいシアン色、完全不透明
            width=1.5,  # 適度な太さ
            parent=self.view.scene
        )
        
        return orbit_line
    
    def _get_distance_to_camera(self, position: np.ndarray) -> float:
        """
        カメラからの距離を計算
        
        Args:
            position: 世界座標での位置
            
        Returns:
            カメラからの距離
        """
        camera_center = np.array(self.camera.center)
        distance_vector = position - camera_center
        return np.linalg.norm(distance_vector)
    
    def _determine_lod_level(self, distance: float) -> str:
        """
        距離に基づいてLODレベルを決定
        
        Args:
            distance: カメラからの距離
            
        Returns:
            LODレベル ('high', 'medium', 'low')
        """
        if not self.lod_enabled:
            return 'high'
        
        if distance <= self.lod_distance_thresholds['high']:
            return 'high'
        elif distance <= self.lod_distance_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _create_planet_sphere_with_lod(self, planet_radius: float, color: tuple, lod_level: str) -> scene.visuals.Sphere:
        """
        LODレベルに応じた惑星球体を作成
        
        Args:
            planet_radius: 惑星半径
            color: 色
            lod_level: LODレベル
            
        Returns:
            惑星球体
        """
        subdivisions = self.lod_sphere_subdivisions[lod_level]
        
        # LODレベルに応じた球体作成
        sphere = scene.visuals.Sphere(
            radius=planet_radius,
            color=color,
            subdivisions=subdivisions,
            parent=self.view.scene
        )
        
        return sphere
    
    def update_planet_position(self, planet_name: str, position: np.ndarray) -> None:
        """
        惑星の位置を更新（LOD自動調整付き）
        
        Args:
            planet_name: 惑星名
            position: 新しい位置 (AU)
        """
        if planet_name not in self.planet_visuals:
            return
        
        visual_data = self.planet_visuals[planet_name]
        
        # 位置はすでにAU単位なので、そのまま使用
        scaled_position = position
        
        # カメラからの距離を計算してLODレベルを決定
        distance_to_camera = self._get_distance_to_camera(scaled_position)
        new_lod_level = self._determine_lod_level(distance_to_camera)
        
        # LODレベルが変更された場合、球体を再作成
        if new_lod_level != visual_data['lod_level']:
            self._update_planet_lod(planet_name, new_lod_level)
        
        # 球体の位置を更新
        sphere = visual_data['sphere']
        sphere.transform = STTransform(translate=scaled_position)
        
        # ラベルの位置を更新（惑星の少し上に配置）
        label = visual_data['label']
        label_offset = np.array([0, 0, 0.1])  # 少し上にオフセット
        label.transform = STTransform(translate=scaled_position + label_offset)
    
    def _update_planet_lod(self, planet_name: str, new_lod_level: str) -> None:
        """
        惑星のLODレベルを更新
        
        Args:
            planet_name: 惑星名
            new_lod_level: 新しいLODレベル
        """
        if planet_name not in self.planet_visuals:
            return
        
        visual_data = self.planet_visuals[planet_name]
        old_sphere = visual_data['sphere']
        
        # 現在の位置と変換を保存
        current_transform = old_sphere.transform
        
        # 新しいLODレベルで球体を再作成
        new_sphere = self._create_planet_sphere_with_lod(
            visual_data['base_radius'],
            visual_data['base_color'],
            new_lod_level
        )
        
        # 位置を復元
        new_sphere.transform = current_transform
        
        # 選択状態の復元
        # Vispyでは色を直接変更できないため、選択状態は別の方法で表現
        
        # 古い球体を削除
        if old_sphere.parent:
            old_sphere.parent = None
        
        # 新しい球体に更新
        visual_data['sphere'] = new_sphere
        visual_data['lod_level'] = new_lod_level
    
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
        # STTransformは回転をサポートしないため、MatrixTransformを使用
        from vispy.visuals.transforms import MatrixTransform
        import numpy as np
        
        # 回転行列を作成
        cos_theta = np.cos(np.radians(rotation_angle))
        sin_theta = np.sin(np.radians(rotation_angle))
        rotation_matrix = np.array([
            [cos_theta, -sin_theta, 0, 0],
            [sin_theta, cos_theta, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # 平行移動行列
        translation_matrix = np.eye(4)
        # positionが4要素の場合（同次座標）、最初の3要素のみ使用
        if len(position) == 4:
            translation_matrix[:3, 3] = position[:3]
        else:
            translation_matrix[:3, 3] = position
        
        # 変換を組み合わせる
        transform_matrix = translation_matrix @ rotation_matrix
        sphere.transform = MatrixTransform(transform_matrix)
    
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
            # Vispyでは色を直接変更できないため、選択解除時は何もしない
            # 将来的には選択リングなどで表現することを検討
        
        # 新しい選択を適用
        self.selected_planet = planet_name
        if planet_name and planet_name in self.planet_visuals:
            visual_data = self.planet_visuals[planet_name]
            sphere = visual_data['sphere']
            # 選択状態を示すために明るくする
            # Vispyでは色を直接変更できないため、選択時は何もしない
            # 将来的には選択リングなどで表現することを検討
    
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
    
    def set_axes_visibility(self, visible: bool) -> None:
        """
        座標軸の表示/非表示を設定
        
        Args:
            visible: 表示するかどうか
        """
        self.show_axes = visible
        
        if hasattr(self, 'axis') and self.axis:
            self.axis.visible = visible
    
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
        
        # カメラ移動後のLOD更新
        self.update_all_lod()
    
    def update_all_lod(self) -> None:
        """全ての惑星のLODレベルを更新"""
        if not self.lod_enabled:
            return
        
        for planet_name, visual_data in self.planet_visuals.items():
            planet = visual_data['planet']
            planet_position_scaled = planet.position * self.distance_scale
            distance_to_camera = self._get_distance_to_camera(planet_position_scaled)
            new_lod_level = self._determine_lod_level(distance_to_camera)
            
            if new_lod_level != visual_data['lod_level']:
                self._update_planet_lod(planet_name, new_lod_level)
    
    def set_lod_enabled(self, enabled: bool) -> None:
        """
        LODシステムの有効/無効を設定
        
        Args:
            enabled: LODを有効にするかどうか
        """
        self.lod_enabled = enabled
        
        if enabled:
            self.update_all_lod()
        else:
            # 全ての惑星を高詳細に設定
            for planet_name in self.planet_visuals.keys():
                self._update_planet_lod(planet_name, 'high')
    
    def set_lod_thresholds(self, high: float, medium: float, low: float) -> None:
        """
        LOD距離閾値を設定
        
        Args:
            high: 高詳細の距離閾値
            medium: 中詳細の距離閾値
            low: 低詳細の距離閾値
        """
        self.lod_distance_thresholds = {
            'high': high,
            'medium': medium,
            'low': low
        }
        
        # 設定変更後にLODを更新
        if self.lod_enabled:
            self.update_all_lod()
    
    def pick_object(self, x: int, y: int) -> Optional[str]:
        """
        画面座標から3Dオブジェクトを選択
        
        Args:
            x: 画面X座標
            y: 画面Y座標
            
        Returns:
            選択されたオブジェクト名（惑星名）
        """
        # 改良されたピッキング実装
        canvas_size = self.canvas.size
        
        # 画面座標を正規化 (0-1範囲)
        norm_x = x / canvas_size[0]
        norm_y = 1.0 - (y / canvas_size[1])  # Y軸反転
        
        min_distance = float('inf')
        selected_planet = None
        
        for planet_name, visual_data in self.planet_visuals.items():
            planet = visual_data['planet']
            
            # 惑星の3D位置
            planet_position = planet.position * self.distance_scale
            
            # 3D座標を画面座標に投影
            screen_pos = self._world_to_screen(planet_position)
            
            if screen_pos is not None:
                # 画面座標での距離計算
                screen_distance = np.sqrt(
                    (norm_x - screen_pos[0])**2 + 
                    (norm_y - screen_pos[1])**2
                )
                
                # 惑星の見かけの大きさを考慮した選択範囲
                planet_radius = max(0.002, planet.radius * self.planet_scale * self.distance_scale)
                selection_threshold = max(0.05, planet_radius * 20)  # 画面上での選択範囲
                
                if screen_distance < selection_threshold and screen_distance < min_distance:
                    min_distance = screen_distance
                    selected_planet = planet_name
        
        return selected_planet
    
    def _world_to_screen(self, world_pos: np.ndarray) -> Optional[np.ndarray]:
        """
        ワールド座標を画面座標に変換
        
        Args:
            world_pos: ワールド座標
            
        Returns:
            正規化された画面座標 [0-1]
        """
        try:
            # カメラの状態を取得
            center = np.array(self.camera.center)
            distance = self.camera.distance
            elevation = np.radians(self.camera.elevation)
            azimuth = np.radians(self.camera.azimuth)
            
            # カメラ位置計算
            camera_x = center[0] + distance * np.cos(elevation) * np.cos(azimuth)
            camera_y = center[1] + distance * np.cos(elevation) * np.sin(azimuth)
            camera_z = center[2] + distance * np.sin(elevation)
            camera_pos = np.array([camera_x, camera_y, camera_z])
            
            # オブジェクトからカメラへの相対位置
            relative_pos = world_pos - center
            
            # カメラ方向ベクトル（中心を向く）
            camera_dir = center - camera_pos
            camera_dir = camera_dir / np.linalg.norm(camera_dir)
            
            # 右方向ベクトル
            up_vector = np.array([0, 0, 1])
            right_vector = np.cross(camera_dir, up_vector)
            if np.linalg.norm(right_vector) > 0:
                right_vector = right_vector / np.linalg.norm(right_vector)
            else:
                right_vector = np.array([1, 0, 0])
            
            # 実際の上方向ベクトル
            actual_up = np.cross(right_vector, camera_dir)
            
            # 投影計算
            projected_x = np.dot(relative_pos, right_vector)
            projected_y = np.dot(relative_pos, actual_up)
            depth = np.dot(relative_pos, camera_dir)
            
            if depth > 0:  # オブジェクトがカメラの前にある
                # FOVを考慮した正規化
                fov_factor = np.tan(np.radians(self.camera.fov / 2))
                screen_x = (projected_x / (depth * fov_factor)) * 0.5 + 0.5
                screen_y = (projected_y / (depth * fov_factor)) * 0.5 + 0.5
                
                # 画面範囲内チェック
                if 0 <= screen_x <= 1 and 0 <= screen_y <= 1:
                    return np.array([screen_x, screen_y])
            
            return None
            
        except Exception:
            # エラー時はNoneを返す
            return None
    
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
        # LOD統計を計算
        lod_stats = {'high': 0, 'medium': 0, 'low': 0}
        for visual_data in self.planet_visuals.values():
            lod_level = visual_data.get('lod_level', 'high')
            lod_stats[lod_level] += 1
        
        return {
            'planet_count': len(self.planet_visuals),
            'show_orbits': self.show_orbits,
            'show_labels': self.show_labels,
            'scale_factor': self.scale_factor,
            'selected_planet': self.selected_planet,
            'camera_distance': self.camera.distance,
            'camera_center': self.camera.center,
            'lod_enabled': self.lod_enabled,
            'lod_statistics': lod_stats,
            'lod_thresholds': self.lod_distance_thresholds
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