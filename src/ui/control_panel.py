"""
制御パネルクラスの実装

シミュレーション制御、時間設定、表示オプションなどの
ユーザー操作インターフェースを提供します。
"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QSlider, QLabel, QComboBox, QCheckBox,
    QGroupBox, QSpinBox, QDoubleSpinBox, QFrame,
    QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette


class ControlPanel(QWidget):
    """
    シミュレーション制御パネル
    
    時間制御、ビュー制御、表示オプションなどの
    ユーザーインターフェースを提供します。
    """
    
    # シグナル定義
    play_pause_clicked = pyqtSignal()
    time_scale_changed = pyqtSignal(float)
    reset_view_clicked = pyqtSignal()
    planet_focus_requested = pyqtSignal(str)
    display_option_changed = pyqtSignal(str, bool)  # (オプション名, 有効/無効)
    camera_preset_selected = pyqtSignal(str)
    
    def __init__(self):
        """制御パネルの初期化"""
        super().__init__()
        
        # 状態管理
        self.is_playing = False
        self.current_time_scale = 1.0
        self.current_date = "2000-01-01 12:00:00"
        
        # 惑星リスト
        self.planet_names = [
            "水星", "金星", "地球", "火星", 
            "木星", "土星", "天王星", "海王星"
        ]
        
        # UI初期化
        self._init_ui()
        self._setup_connections()
    
    def _init_ui(self) -> None:
        """UIコンポーネントの初期化"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # タイトル
        title_label = QLabel("シミュレーション制御")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 時間制御セクション
        self._create_time_control_section(main_layout)
        
        # 表示制御セクション
        self._create_display_control_section(main_layout)
        
        # ビュー制御セクション
        self._create_view_control_section(main_layout)
        
        # 惑星選択セクション
        self._create_planet_selection_section(main_layout)
        
        # ストレッチを追加して下部に余白を作る
        main_layout.addStretch()
        
        # パネルのスタイル設定
        self.setMaximumWidth(350)
        self.setMinimumWidth(280)
    
    def _create_time_control_section(self, parent_layout: QVBoxLayout) -> None:
        """時間制御セクションの作成"""
        # グループボックス
        time_group = QGroupBox("時間制御")
        parent_layout.addWidget(time_group)
        
        layout = QVBoxLayout(time_group)
        
        # 現在時刻表示
        self.time_label = QLabel(self.current_date)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        layout.addWidget(self.time_label)
        
        # 再生/一時停止ボタン
        button_layout = QHBoxLayout()
        
        self.play_pause_button = QPushButton("▶ 再生")
        self.play_pause_button.setMinimumHeight(35)
        button_layout.addWidget(self.play_pause_button)
        
        self.reset_button = QPushButton("⏹ リセット")
        self.reset_button.setMinimumHeight(35)
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        
        # 時間倍率制御
        time_scale_layout = QVBoxLayout()
        
        time_scale_label = QLabel("時間倍率")
        time_scale_layout.addWidget(time_scale_label)
        
        # スライダー
        self.time_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_scale_slider.setMinimum(-20)  # 0.1倍
        self.time_scale_slider.setMaximum(50)   # 1000倍
        self.time_scale_slider.setValue(0)      # 1倍
        self.time_scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.time_scale_slider.setTickInterval(10)
        time_scale_layout.addWidget(self.time_scale_slider)
        
        # 倍率表示
        scale_display_layout = QHBoxLayout()
        self.time_scale_display = QLabel("x1.0")
        self.time_scale_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scale_display_layout.addWidget(self.time_scale_display)
        
        # プリセットボタン
        preset_layout = QHBoxLayout()
        self.speed_presets = [
            ("1日/秒", 86400.0),
            ("1週/秒", 604800.0),
            ("1月/秒", 2629746.0),
            ("1年/秒", 31556952.0)
        ]
        
        for name, scale in self.speed_presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, s=scale: self._set_time_scale_preset(s))
            preset_layout.addWidget(btn)
        
        time_scale_layout.addLayout(scale_display_layout)
        time_scale_layout.addLayout(preset_layout)
        layout.addLayout(time_scale_layout)
    
    def _create_display_control_section(self, parent_layout: QVBoxLayout) -> None:
        """表示制御セクションの作成"""
        # グループボックス
        display_group = QGroupBox("表示オプション")
        parent_layout.addWidget(display_group)
        
        layout = QVBoxLayout(display_group)
        
        # チェックボックスオプション
        self.display_options = {
            'show_orbits': QCheckBox("軌道線を表示"),
            'show_labels': QCheckBox("惑星名を表示"),
            'show_trails': QCheckBox("軌道軌跡を表示"),
            'show_axes': QCheckBox("座標軸を表示"),
            'show_grid': QCheckBox("距離グリッドを表示")
        }
        
        # デフォルト状態設定
        self.display_options['show_orbits'].setChecked(True)
        self.display_options['show_labels'].setChecked(True)
        self.display_options['show_axes'].setChecked(True)
        
        for checkbox in self.display_options.values():
            layout.addWidget(checkbox)
        
        # スケール制御
        scale_layout = QVBoxLayout()
        
        # 惑星サイズスケール
        planet_scale_layout = QHBoxLayout()
        planet_scale_layout.addWidget(QLabel("惑星サイズ:"))
        
        self.planet_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.planet_scale_slider.setMinimum(1)
        self.planet_scale_slider.setMaximum(50)
        self.planet_scale_slider.setValue(10)  # 10倍
        planet_scale_layout.addWidget(self.planet_scale_slider)
        
        self.planet_scale_label = QLabel("x10")
        planet_scale_layout.addWidget(self.planet_scale_label)
        
        scale_layout.addLayout(planet_scale_layout)
        
        # 距離スケール
        distance_scale_layout = QHBoxLayout()
        distance_scale_layout.addWidget(QLabel("距離スケール:"))
        
        self.distance_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.distance_scale_slider.setMinimum(1)
        self.distance_scale_slider.setMaximum(100)
        self.distance_scale_slider.setValue(10)  # 1.0倍
        distance_scale_layout.addWidget(self.distance_scale_slider)
        
        self.distance_scale_label = QLabel("x1.0")
        distance_scale_layout.addWidget(self.distance_scale_label)
        
        scale_layout.addLayout(distance_scale_layout)
        layout.addLayout(scale_layout)
    
    def _create_view_control_section(self, parent_layout: QVBoxLayout) -> None:
        """ビュー制御セクションの作成"""
        # グループボックス
        view_group = QGroupBox("ビュー制御")
        parent_layout.addWidget(view_group)
        
        layout = QVBoxLayout(view_group)
        
        # ビューリセットボタン
        self.reset_view_button = QPushButton("🏠 ビューリセット")
        self.reset_view_button.setMinimumHeight(30)
        layout.addWidget(self.reset_view_button)
        
        # カメラプリセット
        preset_layout = QVBoxLayout()
        preset_layout.addWidget(QLabel("カメラプリセット:"))
        
        self.camera_preset_combo = QComboBox()
        self.camera_preset_combo.addItems([
            "パースペクティブ",
            "上面図",
            "側面図",
            "正面図"
        ])
        preset_layout.addWidget(self.camera_preset_combo)
        
        layout.addLayout(preset_layout)
        
        # 追跡制御
        tracking_layout = QVBoxLayout()
        tracking_layout.addWidget(QLabel("カメラ追跡:"))
        
        self.tracking_combo = QComboBox()
        self.tracking_combo.addItem("追跡なし")
        self.tracking_combo.addItems(self.planet_names)
        tracking_layout.addWidget(self.tracking_combo)
        
        layout.addLayout(tracking_layout)
    
    def _create_planet_selection_section(self, parent_layout: QVBoxLayout) -> None:
        """惑星選択セクションの作成"""
        # グループボックス
        planet_group = QGroupBox("惑星選択")
        parent_layout.addWidget(planet_group)
        
        layout = QVBoxLayout(planet_group)
        
        # 惑星ボタングリッド
        grid_layout = QGridLayout()
        
        self.planet_buttons = {}
        for i, planet_name in enumerate(self.planet_names):
            btn = QPushButton(planet_name)
            btn.setMinimumHeight(30)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=planet_name: self._on_planet_selected(name))
            
            row = i // 2
            col = i % 2
            grid_layout.addWidget(btn, row, col)
            
            self.planet_buttons[planet_name] = btn
        
        layout.addLayout(grid_layout)
        
        # 全選択解除ボタン
        clear_selection_btn = QPushButton("選択解除")
        clear_selection_btn.clicked.connect(self._clear_planet_selection)
        layout.addWidget(clear_selection_btn)
    
    def _setup_connections(self) -> None:
        """シグナル・スロット接続の設定"""
        # 時間制御
        self.play_pause_button.clicked.connect(self._on_play_pause_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.time_scale_slider.valueChanged.connect(self._on_time_scale_changed)
        
        # 表示オプション
        for option_name, checkbox in self.display_options.items():
            checkbox.toggled.connect(
                lambda checked, name=option_name: self.display_option_changed.emit(name, checked)
            )
        
        # スケール制御
        self.planet_scale_slider.valueChanged.connect(self._on_planet_scale_changed)
        self.distance_scale_slider.valueChanged.connect(self._on_distance_scale_changed)
        
        # ビュー制御
        self.reset_view_button.clicked.connect(self.reset_view_clicked.emit)
        self.camera_preset_combo.currentTextChanged.connect(self._on_camera_preset_changed)
        self.tracking_combo.currentTextChanged.connect(self._on_tracking_changed)
    
    def _on_play_pause_clicked(self) -> None:
        """再生/一時停止ボタンクリック処理"""
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_pause_button.setText("⏸ 一時停止")
        else:
            self.play_pause_button.setText("▶ 再生")
        
        self.play_pause_clicked.emit()
    
    def _on_reset_clicked(self) -> None:
        """リセットボタンクリック処理"""
        # アニメーション停止
        if self.is_playing:
            self._on_play_pause_clicked()
        
        # 時間をリセット
        self.update_time_display("2000-01-01 12:00:00")
    
    def _on_time_scale_changed(self, value: int) -> None:
        """時間倍率スライダー変更処理"""
        # スライダー値を倍率に変換（対数スケール）
        # -20から50の範囲を0.01倍から1000倍にマッピング
        scale = 10 ** (value / 10.0)
        
        self.current_time_scale = scale
        
        # 表示フォーマットを改善
        if scale >= 1.0:
            if scale >= 100:
                self.time_scale_display.setText(f"x{scale:.0f}")
            elif scale >= 10:
                self.time_scale_display.setText(f"x{scale:.1f}")
            else:
                self.time_scale_display.setText(f"x{scale:.2f}")
        else:
            self.time_scale_display.setText(f"x{scale:.3f}")
        
        self.time_scale_changed.emit(scale)
    
    def _set_time_scale_preset(self, scale: float) -> None:
        """時間倍率プリセット設定"""
        # スライダー値に変換（対数スケールの逆変換）
        import math
        slider_value = int(10 * math.log10(scale))
        # 範囲チェック
        slider_value = max(-20, min(50, slider_value))
        self.time_scale_slider.setValue(slider_value)
    
    def _on_planet_scale_changed(self, value: int) -> None:
        """惑星サイズスケール変更処理"""
        scale = value / 10.0
        self.planet_scale_label.setText(f"x{scale:.1f}")
        self.display_option_changed.emit("planet_scale", scale)
    
    def _on_distance_scale_changed(self, value: int) -> None:
        """距離スケール変更処理"""
        scale = value / 10.0
        self.distance_scale_label.setText(f"x{scale:.1f}")
        self.display_option_changed.emit("distance_scale", scale)
    
    def _on_camera_preset_changed(self, preset_name: str) -> None:
        """カメラプリセット変更処理"""
        preset_map = {
            "パースペクティブ": "perspective",
            "上面図": "top",
            "側面図": "side",
            "正面図": "front"
        }
        
        if preset_name in preset_map:
            self.camera_preset_selected.emit(preset_map[preset_name])
    
    def _on_tracking_changed(self, target: str) -> None:
        """追跡対象変更処理"""
        if target == "追跡なし":
            # 追跡停止のシグナル（空文字で表現）
            self.planet_focus_requested.emit("")
        elif target in self.planet_names:
            self.planet_focus_requested.emit(target)
    
    def _on_planet_selected(self, planet_name: str) -> None:
        """惑星選択処理"""
        # 他のボタンの選択を解除
        for name, btn in self.planet_buttons.items():
            if name != planet_name:
                btn.setChecked(False)
        
        # 選択された惑星にフォーカス
        if self.planet_buttons[planet_name].isChecked():
            self.planet_focus_requested.emit(planet_name)
            # 追跡コンボボックスも更新
            self.tracking_combo.setCurrentText(planet_name)
        else:
            # 選択解除
            self._clear_planet_selection()
    
    def _clear_planet_selection(self) -> None:
        """惑星選択解除"""
        for btn in self.planet_buttons.values():
            btn.setChecked(False)
        
        self.tracking_combo.setCurrentText("追跡なし")
        self.planet_focus_requested.emit("")
    
    def update_time_display(self, datetime_str: str) -> None:
        """現在時刻表示を更新"""
        self.current_date = datetime_str
        self.time_label.setText(datetime_str)
    
    def set_animation_state(self, is_playing: bool) -> None:
        """アニメーション状態を設定"""
        if self.is_playing != is_playing:
            self.is_playing = is_playing
            
            if self.is_playing:
                self.play_pause_button.setText("⏸ 一時停止")
            else:
                self.play_pause_button.setText("▶ 再生")
    
    def get_display_options(self) -> Dict[str, bool]:
        """現在の表示オプション状態を取得"""
        return {
            name: checkbox.isChecked()
            for name, checkbox in self.display_options.items()
        }
    
    def set_display_option(self, option_name: str, enabled: bool) -> None:
        """表示オプションを設定"""
        if option_name in self.display_options:
            self.display_options[option_name].setChecked(enabled)
    
    def get_current_time_scale(self) -> float:
        """現在の時間倍率を取得"""
        return self.current_time_scale
    
    def __str__(self) -> str:
        """文字列表現"""
        status = "再生中" if self.is_playing else "停止中"
        return f"ControlPanel ({status}, 倍率: x{self.current_time_scale:.1f})"