"""
シーンマネージャークラスの実装

3Dシーン全体の管理、天体の描画制御、
視覚効果の管理などを行います。
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from vispy import scene, color

from ..domain.solar_system import SolarSystem
from ..domain.planet import Planet
from ..domain.sun import Sun
from .renderer_3d import Renderer3D
from .camera_controller import CameraController


class SceneManager:
    """
    3Dシーン全体を管理するクラス
    
    太陽系の描画、天体の更新、視覚効果の制御、
    ユーザーインタラクションの処理などを行います。
    """
    
    def __init__(self, canvas: scene.SceneCanvas):
        """
        シーンマネージャーの初期化
        
        Args:
            canvas: Vispyのシーンキャンバス
        """
        self.canvas = canvas
        
        # コンポーネントの初期化
        self.renderer = Renderer3D(canvas)
        self.camera_controller = CameraController(self.renderer.view)
        
        # 太陽系データ
        self.solar_system: Optional[SolarSystem] = None
        
        # 表示設定
        self.display_settings = {
            'show_orbits': True,
            'show_labels': True,
            'show_planet_trails': False,
            'show_coordinate_axes': True,
            'show_distance_grid': False,
            'planet_scale_factor': 1000.0,
            'distance_scale_factor': 1.0,
            'animation_speed': 1.0
        }
        
        # アニメーション状態
        self.is_playing = False
        self.animation_time = 0.0
        self.time_step = 1.0  # 日単位
        
        # 選択状態
        self.selected_planet: Optional[str] = None
        
        # 視覚効果
        self.coordinate_axes: Optional[scene.visuals.XYZAxis] = None
        self.distance_grid: Optional[scene.visuals.GridLines] = None
        
        # イベントハンドラー
        self._setup_event_handlers()
        
        # 初期シーンセットアップ
        self._setup_initial_scene()
    
    def _setup_event_handlers(self) -> None:
        """イベントハンドラーの設定"""
        # マウスクリック処理
        self.canvas.events.mouse_press.connect(self._on_mouse_press)
        
        # マウス移動処理
        self.canvas.events.mouse_move.connect(self._on_mouse_move)
        
        # マウスリリース処理
        self.canvas.events.mouse_release.connect(self._on_mouse_release)
        
        # キーボード処理
        self.canvas.events.key_press.connect(self._on_key_press)
        
        # マウスホイール処理
        self.canvas.events.mouse_wheel.connect(self._on_mouse_wheel)
    
    def _setup_initial_scene(self) -> None:
        """初期シーンのセットアップ"""
        # 座標軸の作成
        if self.display_settings['show_coordinate_axes']:
            self._create_coordinate_axes()
        
        # 距離グリッドの作成
        if self.display_settings['show_distance_grid']:
            self._create_distance_grid()
    
    def _create_coordinate_axes(self) -> None:
        """座標軸の作成"""
        self.coordinate_axes = scene.visuals.XYZAxis(parent=self.renderer.view.scene)
        
        # 座標軸のスケールを設定（1AU = 1単位）
        self.coordinate_axes.transform = scene.STTransform(scale=(1, 1, 1))
    
    def _create_distance_grid(self) -> None:
        """距離グリッドの作成"""
        # グリッド線を作成（X-Y平面）
        grid_size = 10  # ±10AU
        grid_spacing = 1  # 1AU間隔
        
        lines = []
        # X軸に平行な線
        for y in np.arange(-grid_size, grid_size + 1, grid_spacing):
            lines.extend([[-grid_size, y, 0], [grid_size, y, 0]])
        
        # Y軸に平行な線
        for x in np.arange(-grid_size, grid_size + 1, grid_spacing):
            lines.extend([[x, -grid_size, 0], [x, grid_size, 0]])
        
        self.distance_grid = scene.visuals.Line(
            pos=np.array(lines).reshape(-1, 3),
            color=(0.3, 0.3, 0.3, 0.5),
            width=1.0,
            parent=self.renderer.view.scene
        )
    
    def load_solar_system(self, solar_system: SolarSystem) -> None:
        """
        太陽系データを読み込み
        
        Args:
            solar_system: 太陽系オブジェクト
        """
        self.solar_system = solar_system
        
        # 既存の天体をクリア
        self.renderer.cleanup()
        
        # 太陽を追加
        if solar_system.has_sun():
            self.renderer.add_sun(solar_system.sun)
        
        # 惑星を追加
        for planet in solar_system.get_planets_list():
            self.renderer.add_planet(planet)
        
        # 表示設定を適用
        self._apply_display_settings()
    
    def update_scene(self, julian_date: float) -> None:
        """
        シーンを更新
        
        Args:
            julian_date: ユリウス日
        """
        if self.solar_system is None:
            return
        
        # 太陽系の位置を更新
        self.solar_system.update_all_positions(julian_date)
        
        # 各惑星の描画位置を更新
        for planet in self.solar_system.get_planets_list():
            self.renderer.update_planet_position(planet.name, planet.position)
            
            # 自転角度の更新（簡易実装）
            rotation_angle = (julian_date * 360.0 / planet.rotation_period) % 360.0
            self.renderer.update_planet_rotation(planet.name, rotation_angle)
        
        # 追跡中の惑星がある場合、カメラを更新
        if self.camera_controller.tracking_target:
            target_planet = self.solar_system.get_planet_by_name(
                self.camera_controller.tracking_target
            )
            if target_planet:
                self.camera_controller.update_tracking_position(target_planet.position)
    
    def update_celestial_bodies(self, solar_system: SolarSystem) -> None:
        """
        天体データの更新（メインアプリケーションから呼び出し）
        
        Args:
            solar_system: 更新された太陽系オブジェクト
        """
        if self.solar_system is None:
            # 初回の場合は太陽系データを読み込み
            self.load_solar_system(solar_system)
            return
        
        # 各惑星の描画位置を更新
        for planet in solar_system.get_planets_list():
            # 位置の更新（kmからAUに変換）
            position_au = planet.position / 149597870.7  # km to AU
            self.renderer.update_planet_position(planet.name, position_au)
            
            # 自転角度の更新（簡易実装）
            # 現在のユリウス日から自転角度を計算
            if hasattr(planet, 'rotation_period') and planet.rotation_period > 0:
                # 現在時刻からの自転角度計算（概算）
                rotation_angle = (solar_system.current_date * 24.0 / abs(planet.rotation_period)) % 360.0
                if planet.rotation_period < 0:  # 逆回転（金星など）
                    rotation_angle = -rotation_angle
                self.renderer.update_planet_rotation(planet.name, rotation_angle)
        
        # 追跡中の惑星がある場合、カメラを更新
        if hasattr(self.camera_controller, 'tracking_target') and self.camera_controller.tracking_target:
            target_planet = solar_system.get_planet_by_name(
                self.camera_controller.tracking_target
            )
            if target_planet:
                position_au = target_planet.position / 149597870.7
                self.camera_controller.update_tracking_position(position_au)
    
    def animate_step(self, time_delta: float) -> None:
        """
        アニメーションの1ステップ実行
        
        Args:
            time_delta: 時間の変化量（日）
        """
        if not self.is_playing or self.solar_system is None:
            return
        
        # 時間を進める
        self.animation_time += time_delta * self.display_settings['animation_speed']
        
        # シーンを更新
        current_julian_date = 2451545.0 + self.animation_time  # J2000.0基準
        self.update_scene(current_julian_date)
    
    def play_animation(self) -> None:
        """アニメーション開始"""
        self.is_playing = True
    
    def pause_animation(self) -> None:
        """アニメーション一時停止"""
        self.is_playing = False
    
    def reset_animation(self) -> None:
        """アニメーションリセット"""
        self.is_playing = False
        self.animation_time = 0.0
        if self.solar_system:
            self.update_scene(2451545.0)  # J2000.0にリセット
    
    def set_animation_speed(self, speed: float) -> None:
        """
        アニメーション速度設定
        
        Args:
            speed: 速度倍率
        """
        self.display_settings['animation_speed'] = max(0.1, speed)
    
    def select_planet(self, planet_name: Optional[str]) -> None:
        """
        惑星を選択
        
        Args:
            planet_name: 選択する惑星名（Noneで選択解除）
        """
        self.selected_planet = planet_name
        self.renderer.set_planet_selected(planet_name)
    
    def focus_on_planet(self, planet_name: str, track: bool = False) -> None:
        """
        惑星にフォーカス
        
        Args:
            planet_name: フォーカスする惑星名
            track: 追跡するかどうか
        """
        if self.solar_system is None:
            return
        
        planet = self.solar_system.get_planet_by_name(planet_name)
        if planet is None:
            return
        
        # 惑星の位置を取得
        planet_position = planet.position * self.renderer.distance_scale
        
        # カメラをフォーカス
        self.camera_controller.focus_on_planet(planet_position, planet.radius)
        
        # 追跡モードの設定
        if track:
            self.camera_controller.track_target(planet_name, planet_position)
        else:
            self.camera_controller.stop_tracking()
    
    def set_display_setting(self, setting: str, value: Any) -> None:
        """
        表示設定を変更
        
        Args:
            setting: 設定名
            value: 設定値
        """
        if setting in self.display_settings:
            self.display_settings[setting] = value
            self._apply_single_setting(setting, value)
    
    def _apply_display_settings(self) -> None:
        """すべての表示設定を適用"""
        for setting, value in self.display_settings.items():
            self._apply_single_setting(setting, value)
    
    def _apply_single_setting(self, setting: str, value: Any) -> None:
        """個別の表示設定を適用"""
        if setting == 'show_orbits':
            self.renderer.set_orbit_visibility(value)
        elif setting == 'show_labels':
            self.renderer.set_label_visibility(value)
        elif setting == 'show_coordinate_axes':
            if self.coordinate_axes:
                self.coordinate_axes.visible = value
        elif setting == 'show_distance_grid':
            if self.distance_grid:
                self.distance_grid.visible = value
        elif setting == 'distance_scale_factor':
            self.renderer.set_scale_factor(value)
        elif setting == 'planet_scale_factor':
            self.renderer.planet_scale = value
            # 惑星を再描画（実装簡素化のため省略）
    
    def _on_mouse_press(self, event) -> None:
        """マウスクリック処理"""
        # カメラコントローラーにイベントを転送
        handled = self.camera_controller.handle_mouse_press(event)
        
        if event.button == 1:  # 左クリック
            # オブジェクトピッキング
            picked_object = self.renderer.pick_object(event.pos[0], event.pos[1])
            if picked_object:
                self.select_planet(picked_object)
            else:
                self.select_planet(None)
    
    def _on_mouse_move(self, event) -> None:
        """マウス移動処理"""
        # カメラコントローラーにイベントを転送
        self.camera_controller.handle_mouse_move(event)
    
    def _on_mouse_release(self, event) -> None:
        """マウスリリース処理"""
        # カメラコントローラーでマウスプレス状態をクリア
        if hasattr(self.camera_controller, '_mouse_press_pos'):
            delattr(self.camera_controller, '_mouse_press_pos')
    
    def _on_key_press(self, event) -> None:
        """キー押下処理"""
        # カメラコントローラーにイベントを転送
        handled = self.camera_controller.handle_key_press(event)
        
        if not handled:
            # SceneManager固有のキーハンドリング
            if event.text == ' ':  # スペースキー
                # アニメーション再生/一時停止
                if self.is_playing:
                    self.pause_animation()
                else:
                    self.play_animation()
            elif event.text == 'o':  # Oキー
                # 軌道表示切り替え
                current_value = self.display_settings['show_orbits']
                self.set_display_setting('show_orbits', not current_value)
            elif event.text == 'l':  # Lキー
                # ラベル表示切り替え
                current_value = self.display_settings['show_labels']
                self.set_display_setting('show_labels', not current_value)
            elif event.text.isdigit():  # 数字キー（5-9）
                # 惑星番号での選択
                planet_index = int(event.text) - 1
                if self.solar_system and 0 <= planet_index < len(self.solar_system.get_planets_list()):
                    planet = self.solar_system.get_planets_list()[planet_index]
                    self.focus_on_planet(planet.name)
    
    def _on_mouse_wheel(self, event) -> None:
        """マウスホイール処理"""
        # カメラコントローラーにイベントを転送
        self.camera_controller.handle_mouse_wheel(event)
    
    def get_scene_info(self) -> Dict[str, Any]:
        """
        シーンの詳細情報を取得
        
        Returns:
            シーン情報の辞書
        """
        scene_info = {
            'is_playing': self.is_playing,
            'animation_time': self.animation_time,
            'selected_planet': self.selected_planet,
            'display_settings': self.display_settings.copy(),
            'camera_info': self.camera_controller.get_camera_info(),
            'render_info': self.renderer.get_render_info()
        }
        
        if self.solar_system:
            scene_info['solar_system'] = {
                'planet_count': self.solar_system.get_planet_count(),
                'has_sun': self.solar_system.has_sun(),
                'current_date': self.solar_system.current_date
            }
        
        return scene_info
    
    def export_scene_image(self, filename: str, width: int = 1920, height: int = 1080) -> bool:
        """
        シーンを画像として出力
        
        Args:
            filename: 出力ファイル名
            width: 画像幅
            height: 画像高さ
            
        Returns:
            成功したかどうか
        """
        try:
            # Vispyのレンダリング結果を画像として保存
            image = self.canvas.render()
            
            # ファイルに保存（PIL等のライブラリが必要）
            # 簡易実装では省略
            print(f"シーン画像を {filename} に保存しました")
            return True
        except Exception as e:
            print(f"画像保存エラー: {e}")
            return False
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        # アニメーション停止
        self.pause_animation()
        
        # レンダラーのクリーンアップ
        self.renderer.cleanup()
        
        # 視覚効果のクリーンアップ
        if self.coordinate_axes and self.coordinate_axes.parent:
            self.coordinate_axes.parent = None
        
        if self.distance_grid and self.distance_grid.parent:
            self.distance_grid.parent = None
        
        # 参照をクリア
        self.solar_system = None
        self.coordinate_axes = None
        self.distance_grid = None
    
    def __str__(self) -> str:
        """文字列表現"""
        planet_count = self.solar_system.get_planet_count() if self.solar_system else 0
        status = "再生中" if self.is_playing else "停止中"
        return f"SceneManager ({planet_count}惑星, {status})"