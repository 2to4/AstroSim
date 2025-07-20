"""
メインウィンドウクラスの実装

PyQt6を使用したアプリケーションのメインウィンドウ。
3Dビューポート、制御パネル、情報パネルを統合します。
"""

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction, QActionGroup

from vispy import scene
from vispy.app import Canvas

from src.ui.control_panel import ControlPanel
from src.ui.info_panel import InfoPanel
from src.visualization.scene_manager import SceneManager
from src.domain.solar_system import SolarSystem


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ
    
    3Dシーンの表示、制御パネル、情報パネルを統合し、
    ユーザーインターフェース全体を管理します。
    """
    
    # シグナル定義
    planet_selected = pyqtSignal(str)  # 惑星選択時
    animation_toggled = pyqtSignal(bool)  # アニメーション切り替え時
    time_scale_changed = pyqtSignal(float)  # 時間倍率変更時
    view_reset_requested = pyqtSignal()  # ビューリセット要求時
    
    def __init__(self, config_manager=None, solar_system: Optional[SolarSystem] = None, time_manager=None):
        """
        メインウィンドウの初期化
        
        Args:
            config_manager: 設定管理オブジェクト
            solar_system: 太陽系データ（オプション）
            time_manager: 時間管理オブジェクト
        """
        super().__init__()
        
        # システムコンポーネント
        self.config_manager = config_manager
        self.time_manager = time_manager
        
        # データ
        self.solar_system = solar_system
        
        # UIコンポーネント
        self.control_panel: Optional[ControlPanel] = None
        self.info_panel: Optional[InfoPanel] = None
        self.canvas: Optional[Canvas] = None
        self.scene_manager: Optional[SceneManager] = None
        
        # レイアウト
        self.central_widget: Optional[QWidget] = None
        self.main_splitter: Optional[QSplitter] = None
        self.side_splitter: Optional[QSplitter] = None
        
        # アニメーションタイマー
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_fps = 60  # FPS
        self.animation_interval = 1000 // self.animation_fps  # ミリ秒
        self.animation_timer.setInterval(self.animation_interval)
        
        # 状態管理
        self.is_fullscreen = False
        self.last_window_state = Qt.WindowState.WindowNoState
        
        # UI初期化
        self._init_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._setup_connections()
        self._setup_keyboard_shortcuts()
        
        # 太陽系データがある場合は読み込み
        if self.solar_system:
            self._load_solar_system()
    
    def _setup_keyboard_shortcuts(self) -> None:
        """キーボードショートカットの設定"""
        # アプリケーション全体のショートカット
        shortcuts = [
            # ファイル操作
            (QKeySequence.StandardKey.Quit, self.close),
            (QKeySequence("Ctrl+R"), self._reset_simulation),
            
            # 表示制御
            (QKeySequence("F11"), self._toggle_fullscreen),
            (QKeySequence("F5"), self._refresh_display),
            (QKeySequence("R"), self._reset_view),
            (QKeySequence("O"), self._toggle_orbits),
            (QKeySequence("L"), self._toggle_labels),
            (QKeySequence("A"), self._toggle_axes),
            
            # プリセットビュー
            (QKeySequence("1"), lambda: self._set_preset_view("top")),
            (QKeySequence("2"), lambda: self._set_preset_view("side")),
            (QKeySequence("3"), lambda: self._set_preset_view("front")),
            (QKeySequence("4"), lambda: self._set_preset_view("perspective")),
            
            # 惑星選択
            (QKeySequence("5"), lambda: self._select_planet_by_index(0)),
            (QKeySequence("6"), lambda: self._select_planet_by_index(1)),
            (QKeySequence("7"), lambda: self._select_planet_by_index(2)),
            (QKeySequence("8"), lambda: self._select_planet_by_index(3)),
            (QKeySequence("9"), lambda: self._select_planet_by_index(4)),
            (QKeySequence("Escape"), self._stop_tracking),
            
            # アニメーション制御
            (QKeySequence("Space"), self._toggle_animation),
            (QKeySequence("Ctrl+Space"), self._pause_animation),
            
            # ヘルプ
            (QKeySequence("F1"), self._show_help),
            (QKeySequence("Ctrl+?"), self._show_keyboard_shortcuts),
        ]
        
        for key_sequence, slot in shortcuts:
            shortcut = QShortcut(key_sequence, self)
            shortcut.activated.connect(slot)
    
    def _reset_simulation(self) -> None:
        """シミュレーションをリセット"""
        if self.time_manager:
            self.time_manager.reset_to_epoch()
        if self.scene_manager:
            self.scene_manager.reset_animation()
            self.scene_manager.camera_controller.reset_view()
        self.update_time_display()
    
    def _toggle_fullscreen(self) -> None:
        """フルスクリーン表示切り替え"""
        if self.isFullScreen():
            self.showNormal()
            # 前回のウィンドウ状態を復元
            if self.last_window_state == Qt.WindowState.WindowMaximized:
                self.showMaximized()
        else:
            self.last_window_state = self.windowState()
            self.showFullScreen()
    
    def _refresh_display(self) -> None:
        """表示を更新"""
        self.update_3d_view()
        self.update_time_display()
        if self.control_panel:
            self.control_panel.update_display()
    
    def _toggle_animation(self) -> None:
        """アニメーション再生/一時停止切り替え"""
        if self.animation_timer.isActive():
            self._pause_animation()
        else:
            self._start_animation()
    
    def _pause_animation(self) -> None:
        """アニメーション一時停止"""
        self.animation_timer.stop()
        if self.scene_manager:
            self.scene_manager.pause_animation()
    
    def _start_animation(self) -> None:
        """アニメーション開始"""
        self.animation_timer.start(self.animation_interval)
        if self.scene_manager:
            self.scene_manager.play_animation()
    
    def _show_help(self) -> None:
        """ヘルプを表示"""
        help_text = """
        <h2>AstroSim - 3D太陽系シミュレーター</h2>
        
        <h3>基本操作:</h3>
        <ul>
            <li><b>マウス左ドラッグ:</b> カメラ回転</li>
            <li><b>マウス右ドラッグ:</b> カメラパン</li>
            <li><b>マウスホイール:</b> ズームイン/アウト</li>
            <li><b>左クリック:</b> 惑星選択</li>
        </ul>
        
        <h3>キーボードショートカット:</h3>
        <ul>
            <li><b>Space:</b> アニメーション再生/一時停止</li>
            <li><b>R:</b> ビューリセット</li>
            <li><b>O:</b> 軌道表示切り替え</li>
            <li><b>L:</b> ラベル表示切り替え</li>
            <li><b>1-4:</b> プリセットビュー（上面/側面/正面/透視図）</li>
            <li><b>5-9:</b> 惑星番号選択</li>
            <li><b>Escape:</b> 追跡停止</li>
            <li><b>F1:</b> ヘルプ表示</li>
            <li><b>F5:</b> 表示更新</li>
            <li><b>F11:</b> フルスクリーン切り替え</li>
            <li><b>Ctrl+R:</b> シミュレーションリセット</li>
            <li><b>Ctrl+Q:</b> 終了</li>
        </ul>
        """
        
        QMessageBox.information(self, "ヘルプ", help_text)
    
    def _show_keyboard_shortcuts(self) -> None:
        """キーボードショートカット一覧を表示"""
        shortcuts_text = """
        <h2>キーボードショートカット一覧</h2>
        
        <table>
        <tr><th>キー</th><th>機能</th></tr>
        <tr><td>Space</td><td>アニメーション再生/一時停止</td></tr>
        <tr><td>R</td><td>ビューリセット</td></tr>
        <tr><td>O</td><td>軌道表示切り替え</td></tr>
        <tr><td>L</td><td>ラベル表示切り替え</td></tr>
        <tr><td>1</td><td>上面ビュー</td></tr>
        <tr><td>2</td><td>側面ビュー</td></tr>
        <tr><td>3</td><td>正面ビュー</td></tr>
        <tr><td>4</td><td>透視図ビュー</td></tr>
        <tr><td>5-9</td><td>惑星番号選択</td></tr>
        <tr><td>Escape</td><td>追跡停止</td></tr>
        <tr><td>F1</td><td>ヘルプ表示</td></tr>
        <tr><td>F5</td><td>表示更新</td></tr>
        <tr><td>F11</td><td>フルスクリーン切り替え</td></tr>
        <tr><td>Ctrl+R</td><td>シミュレーションリセット</td></tr>
        <tr><td>Ctrl+Q</td><td>終了</td></tr>
        </table>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("キーボードショートカット")
        msg.setText(shortcuts_text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.exec()
    
    def _init_ui(self) -> None:
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("AstroSim - 太陽系惑星シミュレーター")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # アイコン設定（仮）
        # self.setWindowIcon(QIcon("assets/icons/astrosim.png"))
        
        # 中央ウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # メインレイアウト
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # スプリッター（3Dビューと制御パネル）
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # 3Dビューポートの作成
        self._create_3d_viewport()
        
        # サイドパネル（制御パネルと情報パネル）
        self._create_side_panels()
        
        # スプリッターのサイズ設定
        self.main_splitter.setSizes([1000, 300])  # 3Dビュー:サイドパネル = 1000:300
    
    def _create_3d_viewport(self) -> None:
        """3Dビューポートの作成"""
        # Vispyキャンバスを作成
        self.canvas = scene.SceneCanvas(
            keys='interactive',
            show=True,
            size=(800, 600),
            bgcolor=(0.0, 0.0, 0.0, 1.0)  # 完全な黒い宇宙背景
        )
        
        # PyQt6ウィジェットとして統合
        canvas_widget = self.canvas.native
        self.main_splitter.addWidget(canvas_widget)
        
        # シーンマネージャーの初期化
        self.scene_manager = SceneManager(self.canvas)
    
    def _create_side_panels(self) -> None:
        """サイドパネルの作成"""
        # サイドパネル用スプリッター（垂直）
        self.side_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.side_splitter)
        
        # 制御パネル
        self.control_panel = ControlPanel()
        self.side_splitter.addWidget(self.control_panel)
        
        # 情報パネル
        self.info_panel = InfoPanel()
        self.side_splitter.addWidget(self.info_panel)
        
        # パネルサイズ設定
        self.side_splitter.setSizes([300, 200])  # 制御:情報 = 300:200
    
    def _create_menu_bar(self) -> None:
        """メニューバーの作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        
        # 太陽系データを開く
        open_action = QAction("太陽系データを開く(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("太陽系データファイルを開きます")
        open_action.triggered.connect(self._open_solar_system)
        file_menu.addAction(open_action)
        
        # 画像として保存
        save_image_action = QAction("画像として保存(&S)", self)
        save_image_action.setShortcut(QKeySequence("Ctrl+S"))
        save_image_action.setStatusTip("現在のシーンを画像として保存します")
        save_image_action.triggered.connect(self._save_scene_image)
        file_menu.addAction(save_image_action)
        
        file_menu.addSeparator()
        
        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("アプリケーションを終了します")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")
        
        # フルスクリーン
        fullscreen_action = QAction("フルスクリーン(&F)", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.setStatusTip("フルスクリーン表示を切り替えます")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        # ビューリセット
        reset_view_action = QAction("ビューリセット(&R)", self)
        reset_view_action.setShortcut(QKeySequence("R"))
        reset_view_action.setStatusTip("カメラビューを初期位置にリセットします")
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)
        
        # シミュレーションメニュー
        sim_menu = menubar.addMenu("シミュレーション(&S)")
        
        # 再生/一時停止
        play_pause_action = QAction("再生/一時停止(&P)", self)
        play_pause_action.setShortcut(QKeySequence("Space"))
        play_pause_action.setStatusTip("シミュレーションの再生/一時停止を切り替えます")
        play_pause_action.triggered.connect(self._toggle_animation)
        sim_menu.addAction(play_pause_action)
        
        # リセット
        reset_sim_action = QAction("リセット(&R)", self)
        reset_sim_action.setShortcut(QKeySequence("Ctrl+R"))
        reset_sim_action.setStatusTip("シミュレーションを初期状態にリセットします")
        reset_sim_action.triggered.connect(self._reset_simulation)
        sim_menu.addAction(reset_sim_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        
        # キーボードショートカット
        shortcuts_action = QAction("キーボードショートカット(&K)", self)
        shortcuts_action.setStatusTip("キーボードショートカットを表示します")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        # バージョン情報
        about_action = QAction("AstroSimについて(&A)", self)
        about_action.setStatusTip("AstroSimのバージョン情報を表示します")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self) -> None:
        """ツールバーの作成"""
        toolbar = self.addToolBar("メイン")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # 再生/一時停止
        play_action = QAction("再生", self)
        play_action.setStatusTip("シミュレーション再生")
        play_action.triggered.connect(self._toggle_animation)
        toolbar.addAction(play_action)
        
        # リセット
        reset_action = QAction("リセット", self)
        reset_action.setStatusTip("シミュレーションリセット")
        reset_action.triggered.connect(self._reset_simulation)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
        # ビューリセット
        view_reset_action = QAction("ビューリセット", self)
        view_reset_action.setStatusTip("カメラビューリセット")
        view_reset_action.triggered.connect(self._reset_view)
        toolbar.addAction(view_reset_action)
    
    def _create_status_bar(self) -> None:
        """ステータスバーの作成"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("準備完了")
    
    def _setup_connections(self) -> None:
        """シグナル・スロット接続の設定"""
        if self.control_panel:
            # 制御パネルからのシグナル
            self.control_panel.play_pause_clicked.connect(self._toggle_animation)
            self.control_panel.time_scale_changed.connect(self._on_time_scale_changed)
            self.control_panel.reset_view_clicked.connect(self._reset_view)
            self.control_panel.planet_focus_requested.connect(self._focus_on_planet)
        
        # シーンマネージャーからのシグナル（今後実装）
        # self.scene_manager.planet_selected.connect(self._on_planet_selected)
    
    def _load_solar_system(self) -> None:
        """太陽系データの読み込み"""
        if self.solar_system and self.scene_manager:
            self.scene_manager.load_solar_system(self.solar_system)
            self.status_bar.showMessage(f"太陽系データ読み込み完了 ({self.solar_system.get_planet_count()}惑星)")
    
    def _update_animation(self) -> None:
        """アニメーション更新"""
        if self.scene_manager:
            # 1フレームあたりの時間進行（日単位）
            time_delta = 1.0 / self.animation_fps
            self.scene_manager.animate_step(time_delta)
    
    def _toggle_animation(self) -> None:
        """アニメーション再生/一時停止切り替え"""
        if self.scene_manager:
            if self.scene_manager.is_playing:
                self.scene_manager.pause_animation()
                self.animation_timer.stop()
                self.status_bar.showMessage("シミュレーション一時停止")
            else:
                self.scene_manager.play_animation()
                self.animation_timer.start()
                self.status_bar.showMessage("シミュレーション再生中")
            
            self.animation_toggled.emit(self.scene_manager.is_playing)
    
    def _reset_simulation(self) -> None:
        """シミュレーションリセット"""
        if self.scene_manager:
            self.scene_manager.reset_animation()
            self.status_bar.showMessage("シミュレーションをリセットしました")
    
    def _reset_view(self) -> None:
        """ビューリセット"""
        if self.scene_manager:
            self.scene_manager.camera_controller.reset_view()
            self.status_bar.showMessage("ビューをリセットしました")
        self.view_reset_requested.emit()
    
    def _set_preset_view(self, preset: str) -> None:
        """プリセットビューの設定"""
        if self.scene_manager and self.scene_manager.camera_controller:
            self.scene_manager.camera_controller.set_view_preset(preset)
            preset_names = {
                "top": "上面ビュー",
                "side": "側面ビュー", 
                "front": "正面ビュー",
                "perspective": "透視図ビュー"
            }
            preset_name = preset_names.get(preset, preset)
            self.status_bar.showMessage(f"{preset_name}に切り替えました")
    
    def _toggle_orbits(self) -> None:
        """軌道線表示切り替え"""
        if self.scene_manager and self.scene_manager.renderer:
            current_state = self.scene_manager.renderer.show_orbits
            self.scene_manager.renderer.set_orbit_visibility(not current_state)
            state_text = "OFF" if current_state else "ON"
            self.status_bar.showMessage(f"軌道線表示: {state_text}")
    
    def _toggle_labels(self) -> None:
        """ラベル表示切り替え"""
        if self.scene_manager and self.scene_manager.renderer:
            current_state = self.scene_manager.renderer.show_labels
            self.scene_manager.renderer.set_label_visibility(not current_state)
            state_text = "OFF" if current_state else "ON"
            self.status_bar.showMessage(f"ラベル表示: {state_text}")
    
    def _toggle_axes(self) -> None:
        """座標軸表示切り替え"""
        if self.scene_manager and self.scene_manager.renderer:
            current_state = self.scene_manager.renderer.show_axes
            self.scene_manager.renderer.set_axes_visibility(not current_state)
            state_text = "OFF" if current_state else "ON"
            self.status_bar.showMessage(f"座標軸表示: {state_text}")
    
    def _select_planet_by_index(self, index: int) -> None:
        """インデックスによる惑星選択"""
        if self.scene_manager and self.solar_system:
            planets = self.solar_system.get_planets()
            if 0 <= index < len(planets):
                planet = planets[index]
                planet_name = planet.name
                self.scene_manager.select_planet(planet_name)
                self._focus_on_planet(planet_name)
                self.status_bar.showMessage(f"{planet_name}を選択しました")
    
    def _stop_tracking(self) -> None:
        """追跡停止"""
        if self.scene_manager and self.scene_manager.camera_controller:
            self.scene_manager.camera_controller.stop_tracking()
            self.status_bar.showMessage("追跡を停止しました")
    
    def _on_time_scale_changed(self, scale: float) -> None:
        """時間倍率変更処理"""
        # TimeManagerに時間倍率を設定
        if self.time_manager:
            self.time_manager.set_time_scale(scale)
        
        # SceneManagerにアニメーション速度を設定
        if self.scene_manager:
            self.scene_manager.set_animation_speed(scale)
        
        # ステータスバーに表示
        if hasattr(self, 'status_bar') and self.status_bar:
            if scale >= 1.0:
                if scale >= 100:
                    scale_text = f"x{scale:.0f}"
                elif scale >= 10:
                    scale_text = f"x{scale:.1f}"
                else:
                    scale_text = f"x{scale:.2f}"
            else:
                scale_text = f"x{scale:.3f}"
            self.status_bar.showMessage(f"時間倍率: {scale_text}")
        
        self.time_scale_changed.emit(scale)
    
    def _focus_on_planet(self, planet_name: str) -> None:
        """惑星フォーカス"""
        if self.scene_manager:
            self.scene_manager.focus_on_planet(planet_name, track=True)
            self.status_bar.showMessage(f"{planet_name}にフォーカスしました")
    
    def _on_planet_selected(self, planet_name: str) -> None:
        """惑星選択処理"""
        if self.info_panel and self.solar_system:
            planet = self.solar_system.get_planet_by_name(planet_name)
            if planet:
                planet_info = self._get_planet_info(planet)
                self.info_panel.display_planet_info(planet_info)
                self.status_bar.showMessage(f"{planet_name}を選択")
        self.planet_selected.emit(planet_name)
    
    def _get_planet_info(self, planet) -> Dict[str, Any]:
        """惑星情報を取得"""
        # 実装は簡易版
        return {
            'name': planet.name,
            'mass': planet.mass,
            'radius': planet.radius,
            'orbital_period': planet.orbital_elements.get_orbital_period(),
            'distance_from_sun': f"{(planet.position[0]**2 + planet.position[1]**2 + planet.position[2]**2)**0.5 / 149597870.7:.3f} AU"
        }
    
    def _toggle_fullscreen(self) -> None:
        """フルスクリーン切り替え"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True
    
    def _open_solar_system(self) -> None:
        """太陽系データファイルを開く"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "太陽系データファイルを開く",
            "",
            "JSONファイル (*.json);;すべてのファイル (*.*)"
        )
        if filename:
            # TODO: ファイル読み込み実装
            self.status_bar.showMessage(f"ファイル読み込み: {filename}")
    
    def _save_scene_image(self) -> None:
        """シーンを画像として保存"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "シーンを画像として保存",
            "astrosim_scene.png",
            "PNGファイル (*.png);;JPEGファイル (*.jpg);;すべてのファイル (*.*)"
        )
        if filename and self.scene_manager:
            success = self.scene_manager.export_scene_image(filename)
            if success:
                self.status_bar.showMessage(f"画像を保存しました: {filename}")
            else:
                QMessageBox.warning(self, "エラー", "画像の保存に失敗しました")
    
    def _show_shortcuts(self) -> None:
        """キーボードショートカット表示"""
        shortcuts_text = """
キーボードショートカット:

スペース: 再生/一時停止
R: ビューリセット
O: 軌道線表示切り替え
L: ラベル表示切り替え
1-9: 惑星選択
F11: フルスクリーン
Ctrl+O: ファイルを開く
Ctrl+S: 画像として保存
Ctrl+Q: 終了
        """
        QMessageBox.information(self, "キーボードショートカット", shortcuts_text.strip())
    
    def _show_about(self) -> None:
        """バージョン情報表示"""
        about_text = """
AstroSim - 太陽系惑星シミュレーター

バージョン: 1.0.0
開発: Claude Code

太陽系の惑星軌道をリアルタイムで
シミュレーションするアプリケーションです。

技術スタック:
- Python 3.8+
- PyQt6 (GUI)
- Vispy (3D描画)
- NumPy/SciPy (科学計算)
        """
        QMessageBox.about(self, "AstroSimについて", about_text.strip())
    
    def update_3d_view(self) -> None:
        """3D表示の更新（メインアプリケーションから呼び出し）"""
        if self.scene_manager and self.solar_system:
            # 太陽系の現在状態を3Dシーンに反映
            self.scene_manager.update_celestial_bodies(self.solar_system)
            
            # 情報パネルの更新（選択された惑星がある場合）
            if hasattr(self, '_selected_planet') and self._selected_planet:
                planet = self.solar_system.get_planet_by_name(self._selected_planet)
                if planet and self.info_panel:
                    planet_info = self._get_planet_info(planet)
                    self.info_panel.display_planet_info(planet_info)
    
    def update_time_display(self) -> None:
        """時間表示の更新（メインアプリケーションから呼び出し）"""
        if self.time_manager and self.control_panel:
            current_time = self.time_manager.get_current_datetime()
            time_string = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # 制御パネルの時間表示を更新
            if hasattr(self.control_panel, 'update_time_display'):
                self.control_panel.update_time_display(time_string)
            
            # ステータスバーの時間表示を更新
            scale_text = f"x{self.time_manager.time_scale:.1f}" if self.time_manager.time_scale != 1.0 else ""
            status_text = f"時刻: {time_string} {scale_text}".strip()
            self.status_bar.showMessage(status_text)
    
    def get_3d_canvas(self):
        """3DキャンバスのQtウィジェットを取得"""
        if self.scene_manager and hasattr(self.scene_manager, 'canvas'):
            return self.scene_manager.canvas.native
        return None
    
    def set_selected_planet(self, planet_name: str) -> None:
        """選択された惑星を設定"""
        self._selected_planet = planet_name
        self._on_planet_selected(planet_name)
    
    def closeEvent(self, event) -> None:
        """ウィンドウクローズイベント"""
        # アニメーション停止
        self.animation_timer.stop()
        
        # シーンマネージャーのクリーンアップ
        if self.scene_manager:
            self.scene_manager.cleanup()
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "終了確認",
            "AstroSimを終了しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
    
    def set_solar_system(self, solar_system: SolarSystem) -> None:
        """太陽系データを設定"""
        self.solar_system = solar_system
        self._load_solar_system()
    
    def get_scene_info(self) -> Dict[str, Any]:
        """シーン情報を取得"""
        if self.scene_manager:
            return self.scene_manager.get_scene_info()
        return {}
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"MainWindow (太陽系: {self.solar_system.get_planet_count() if self.solar_system else 0}惑星)"