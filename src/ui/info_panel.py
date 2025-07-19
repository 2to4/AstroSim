"""
情報パネルクラスの実装

選択された惑星の詳細情報、軌道データ、
物理的性質などを表示します。
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextBrowser, QGroupBox, QFrame, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QPixmap


class InfoPanel(QWidget):
    """
    惑星情報表示パネル
    
    選択された惑星の軌道データ、物理的性質、
    現在の状態などを詳細に表示します。
    """
    
    # シグナル定義
    planet_info_updated = pyqtSignal(str)  # 惑星名
    
    def __init__(self):
        """情報パネルの初期化"""
        super().__init__()
        
        # 現在表示中の惑星
        self.current_planet: Optional[str] = None
        
        # UI初期化
        self._init_ui()
        
        # 初期状態表示
        self._show_welcome_message()
    
    def _init_ui(self) -> None:
        """UIの初期化"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # タイトル
        title_label = QLabel("天体情報")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 惑星名表示
        self.planet_name_label = QLabel("選択された天体なし")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.planet_name_label.setFont(name_font)
        self.planet_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.planet_name_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 5px;
                padding: 8px;
                margin: 5px;
            }
        """)\n        main_layout.addWidget(self.planet_name_label)
        
        # スクロール可能な情報表示エリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 情報表示ウィジェット
        self.info_widget = QWidget()
        scroll_area.setWidget(self.info_widget)
        main_layout.addWidget(scroll_area)
        
        # 情報ウィジェットのレイアウト
        self.info_layout = QVBoxLayout(self.info_widget)
        self.info_layout.setContentsMargins(5, 5, 5, 5)
        self.info_layout.setSpacing(10)
        
        # パネルのサイズ制約
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
    
    def _show_welcome_message(self) -> None:
        """初期メッセージ表示"""
        welcome_text = """
        <div style='text-align: center; color: #666;'>
        <h3>AstroSim 天体情報パネル</h3>
        <p>惑星をクリックまたは選択すると、<br>
        詳細な情報がここに表示されます。</p>
        
        <hr style='margin: 20px 0;'>
        
        <h4>表示される情報:</h4>
        <ul style='text-align: left;'>
        <li>基本物理データ</li>
        <li>軌道要素</li>
        <li>現在の位置・速度</li>
        <li>軌道の特徴</li>
        </ul>
        </div>
        """
        
        welcome_label = QLabel(welcome_text)
        welcome_label.setWordWrap(True)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.info_layout.addWidget(welcome_label)
        self.info_layout.addStretch()
    
    def display_planet_info(self, planet_data: Dict[str, Any]) -> None:
        """
        惑星情報を表示
        
        Args:
            planet_data: 惑星データの辞書
        """
        # 現在の情報をクリア
        self.clear_info()
        
        planet_name = planet_data.get('name', '不明な天体')
        self.current_planet = planet_name
        self.planet_name_label.setText(planet_name)
        
        # 基本情報セクション
        self._create_basic_info_section(planet_data)
        
        # 軌道情報セクション
        self._create_orbital_info_section(planet_data)
        
        # 現在状態セクション
        self._create_current_state_section(planet_data)
        
        # 物理的性質セクション
        self._create_physical_properties_section(planet_data)
        
        # ストレッチを追加
        self.info_layout.addStretch()
        
        # シグナル発行
        self.planet_info_updated.emit(planet_name)
    
    def _create_basic_info_section(self, planet_data: Dict[str, Any]) -> None:
        """基本情報セクションの作成"""
        group = QGroupBox("基本情報")
        self.info_layout.addWidget(group)
        
        layout = QVBoxLayout(group)
        
        # データグリッド
        grid = QGridLayout()
        
        basic_info = [
            ("質量", self._format_mass(planet_data.get('mass', 0))),
            ("半径", self._format_radius(planet_data.get('radius', 0))),
            ("密度", self._format_density(planet_data)),
            ("重力", self._format_gravity(planet_data)),
            ("脱出速度", self._format_escape_velocity(planet_data))
        ]
        
        for i, (label, value) in enumerate(basic_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_widget = QLabel(value)
            value_widget.setWordWrap(True)
            
            grid.addWidget(label_widget, i, 0)
            grid.addWidget(value_widget, i, 1)
        
        layout.addLayout(grid)
    
    def _create_orbital_info_section(self, planet_data: Dict[str, Any]) -> None:
        """軌道情報セクションの作成"""
        orbital_elements = planet_data.get('orbital_elements')
        if not orbital_elements:
            return
        
        group = QGroupBox("軌道要素")
        self.info_layout.addWidget(group)
        
        layout = QVBoxLayout(group)
        grid = QGridLayout()
        
        orbital_info = [
            ("軌道長半径", f"{orbital_elements.get('semi_major_axis', 0):.6f} AU"),
            ("離心率", f"{orbital_elements.get('eccentricity', 0):.6f}"),
            ("軌道傾斜角", f"{orbital_elements.get('inclination', 0):.3f}°"),
            ("昇交点黄経", f"{orbital_elements.get('longitude_of_ascending_node', 0):.3f}°"),
            ("近日点引数", f"{orbital_elements.get('argument_of_perihelion', 0):.3f}°"),
            ("軌道周期", self._format_orbital_period(planet_data.get('orbital_period', 0)))
        ]
        
        for i, (label, value) in enumerate(orbital_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_widget = QLabel(value)
            value_widget.setWordWrap(True)
            
            grid.addWidget(label_widget, i, 0)
            grid.addWidget(value_widget, i, 1)
        
        layout.addLayout(grid)
        
        # 軌道の特徴
        orbital_features = self._analyze_orbital_features(orbital_elements)
        if orbital_features:
            features_label = QLabel(f"<b>軌道の特徴:</b><br>{orbital_features}")
            features_label.setWordWrap(True)
            layout.addWidget(features_label)
    
    def _create_current_state_section(self, planet_data: Dict[str, Any]) -> None:
        """現在状態セクションの作成"""
        group = QGroupBox("現在の状態")
        self.info_layout.addWidget(group)
        
        layout = QVBoxLayout(group)
        grid = QGridLayout()
        
        # 位置情報
        position = planet_data.get('position', [0, 0, 0])
        distance_from_sun = planet_data.get('distance_from_sun', '計算中')
        
        current_info = [
            ("太陽からの距離", distance_from_sun),
            ("X座標", f"{position[0]/149597870.7:.3f} AU" if len(position) > 0 else "0 AU"),
            ("Y座標", f"{position[1]/149597870.7:.3f} AU" if len(position) > 1 else "0 AU"),
            ("Z座標", f"{position[2]/149597870.7:.3f} AU" if len(position) > 2 else "0 AU"),
            ("軌道速度", self._format_orbital_velocity(planet_data))
        ]
        
        for i, (label, value) in enumerate(current_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            
            grid.addWidget(label_widget, i, 0)
            grid.addWidget(value_widget, i, 1)
        
        layout.addLayout(grid)
    
    def _create_physical_properties_section(self, planet_data: Dict[str, Any]) -> None:
        """物理的性質セクションの作成"""
        group = QGroupBox("物理的性質")
        self.info_layout.addWidget(group)
        
        layout = QVBoxLayout(group)
        
        # 色情報
        color = planet_data.get('color', (0.5, 0.5, 0.5))
        color_text = f"RGB({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})"
        
        # 自転情報
        rotation_period = planet_data.get('rotation_period', 24.0)
        axial_tilt = planet_data.get('axial_tilt', 0.0)
        
        grid = QGridLayout()
        
        physical_info = [
            ("表面色", color_text),
            ("自転周期", f"{rotation_period:.2f} 時間"),
            ("自転軸傾斜", f"{axial_tilt:.1f}°"),
            ("テクスチャ", planet_data.get('texture_path', 'なし'))
        ]
        
        for i, (label, value) in enumerate(physical_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            
            grid.addWidget(label_widget, i, 0)
            grid.addWidget(value_widget, i, 1)
        
        layout.addLayout(grid)
    
    def _format_mass(self, mass: float) -> str:
        """質量をフォーマット"""
        if mass == 0:
            return "データなし"
        
        earth_mass = 5.972e24  # kg
        if mass > earth_mass:
            return f"{mass:.2e} kg ({mass/earth_mass:.2f} 地球質量)"
        else:
            return f"{mass:.2e} kg ({mass/earth_mass:.4f} 地球質量)"
    
    def _format_radius(self, radius: float) -> str:
        """半径をフォーマット"""
        if radius == 0:
            return "データなし"
        
        earth_radius = 6371.0  # km
        return f"{radius:.1f} km ({radius/earth_radius:.3f} 地球半径)"
    
    def _format_density(self, planet_data: Dict[str, Any]) -> str:
        """密度を計算・フォーマット"""
        mass = planet_data.get('mass', 0)
        radius = planet_data.get('radius', 0)
        
        if mass == 0 or radius == 0:
            return "計算不可"
        
        import math
        volume = (4/3) * math.pi * (radius * 1000)**3  # m³
        density = mass / volume  # kg/m³
        
        return f"{density:.0f} kg/m³"
    
    def _format_gravity(self, planet_data: Dict[str, Any]) -> str:
        """表面重力を計算・フォーマット"""
        mass = planet_data.get('mass', 0)
        radius = planet_data.get('radius', 0)
        
        if mass == 0 or radius == 0:
            return "計算不可"
        
        G = 6.67430e-11  # m³ kg⁻¹ s⁻²
        gravity = G * mass / (radius * 1000)**2  # m/s²
        earth_gravity = 9.81  # m/s²
        
        return f"{gravity:.2f} m/s² ({gravity/earth_gravity:.2f} g)"
    
    def _format_escape_velocity(self, planet_data: Dict[str, Any]) -> str:
        """脱出速度を計算・フォーマット"""
        mass = planet_data.get('mass', 0)
        radius = planet_data.get('radius', 0)
        
        if mass == 0 or radius == 0:
            return "計算不可"
        
        import math
        G = 6.67430e-11  # m³ kg⁻¹ s⁻²
        escape_velocity = math.sqrt(2 * G * mass / (radius * 1000))  # m/s
        
        return f"{escape_velocity/1000:.2f} km/s"
    
    def _format_orbital_period(self, period_days: float) -> str:
        """軌道周期をフォーマット"""
        if period_days == 0:
            return "データなし"
        
        years = period_days / 365.25
        if years >= 1:
            return f"{period_days:.1f} 日 ({years:.2f} 年)"
        else:
            return f"{period_days:.1f} 日"
    
    def _format_orbital_velocity(self, planet_data: Dict[str, Any]) -> str:
        """軌道速度をフォーマット"""
        velocity = planet_data.get('velocity', [0, 0, 0])
        if len(velocity) < 3:
            return "計算中"
        
        import math
        speed = math.sqrt(velocity[0]**2 + velocity[1]**2 + velocity[2]**2)
        return f"{speed:.2f} km/s"
    
    def _analyze_orbital_features(self, orbital_elements: Dict[str, Any]) -> str:
        """軌道の特徴を分析"""
        features = []
        
        eccentricity = orbital_elements.get('eccentricity', 0)
        inclination = orbital_elements.get('inclination', 0)
        
        # 軌道の形状
        if eccentricity < 0.05:
            features.append("ほぼ円軌道")
        elif eccentricity < 0.1:
            features.append("やや楕円軌道")
        elif eccentricity < 0.3:
            features.append("楕円軌道")
        else:
            features.append("高い離心率の楕円軌道")
        
        # 軌道傾斜
        if inclination < 5:
            features.append("黄道面にほぼ一致")
        elif inclination < 30:
            features.append("軽微な軌道傾斜")
        else:
            features.append("大きな軌道傾斜")
        
        return "、".join(features)
    
    def display_sun_info(self, sun_data: Dict[str, Any]) -> None:
        """太陽情報を表示"""
        # 太陽専用の情報表示
        self.clear_info()
        
        self.current_planet = "太陽"
        self.planet_name_label.setText("太陽 ☀")
        
        # 太陽の基本情報
        group = QGroupBox("太陽の基本情報")
        self.info_layout.addWidget(group)
        
        layout = QVBoxLayout(group)
        grid = QGridLayout()
        
        sun_info = [
            ("質量", self._format_mass(sun_data.get('mass', 1.989e30))),
            ("半径", f"{sun_data.get('radius', 695700):.0f} km"),
            ("表面温度", f"{sun_data.get('temperature', 5778):.0f} K"),
            ("光度", f"{sun_data.get('luminosity', 3.828e26):.2e} W"),
            ("脱出速度", f"{sun_data.get('escape_velocity', 617.5):.1f} km/s"),
            ("位置", "座標系の原点 (0, 0, 0)")
        ]
        
        for i, (label, value) in enumerate(sun_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            
            grid.addWidget(label_widget, i, 0)
            grid.addWidget(value_widget, i, 1)
        
        layout.addLayout(grid)
        
        # 特徴説明
        description = QLabel("""
        <b>太陽の特徴:</b><br>
        • 太陽系の中心恒星<br>
        • 全質量の99.86%を占める<br>
        • 核融合により光と熱を放射<br>
        • 惑星軌道の重力源
        """)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        self.info_layout.addStretch()
        self.planet_info_updated.emit("太陽")
    
    def clear_info(self) -> None:
        """情報をクリア"""
        # 既存のウィジェットを削除
        while self.info_layout.count():
            child = self.info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 惑星名をクリア
        self.planet_name_label.setText("選択された天体なし")
        self.current_planet = None
    
    def get_current_planet(self) -> Optional[str]:
        """現在表示中の惑星名を取得"""
        return self.current_planet
    
    def update_real_time_data(self, planet_data: Dict[str, Any]) -> None:
        """リアルタイムデータの更新"""
        # 現在の状態セクションのみ更新（効率化）
        if self.current_planet and self.current_planet == planet_data.get('name'):
            # 距離情報のみ更新（簡易実装）
            distance_from_sun = planet_data.get('distance_from_sun', '計算中')
            # 実際の実装では、特定のラベルのみ更新
    
    def __str__(self) -> str:
        """文字列表現"""
        if self.current_planet:
            return f"InfoPanel (表示中: {self.current_planet})"
        else:
            return "InfoPanel (表示なし)"