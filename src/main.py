#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroSim メインアプリケーション

太陽系惑星軌道シミュレーションのメインエントリーポイント。
PyQt6 + Vispy統合によるインタラクティブ3Dアプリケーション。
"""

import sys
import logging
from pathlib import Path
from typing import Optional
import traceback

# PyQt6インポート
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print("PyQt6が見つかりません。以下のコマンドでインストールしてください:")
    print("pip install PyQt6")
    sys.exit(1)

# Vispyインポート
try:
    import vispy
    from vispy import app as vispy_app
    vispy.use('pyqt6')  # PyQt6バックエンドを使用
except ImportError as e:
    print("Vispyが見つかりません。以下のコマンドでインストールしてください:")
    print("pip install vispy")
    sys.exit(1)

# プロジェクトモジュールインポート
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.data.data_loader import DataLoader
    from src.data.config_manager import ConfigManager
    from src.simulation.time_manager import TimeManager
    from src.simulation.physics_engine import PhysicsEngine
    from src.ui.main_window import MainWindow
    from src.visualization.renderer_3d import Renderer3D
    from src.domain.solar_system import SolarSystem
except ImportError as e:
    print(f"モジュールインポートエラー: {e}")
    print("プロジェクト構造を確認してください。")
    traceback.print_exc()
    sys.exit(1)


class AstroSimApplication:
    """
    AstroSimアプリケーション統合管理クラス
    
    全システムレイヤーを統合し、アプリケーション全体の
    ライフサイクルを管理します。
    """
    
    def __init__(self):
        """アプリケーションの初期化"""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        
        # システムコンポーネント
        self.data_loader: Optional[DataLoader] = None
        self.config_manager: Optional[ConfigManager] = None
        self.solar_system: Optional[SolarSystem] = None
        self.time_manager: Optional[TimeManager] = None
        self.physics_engine: Optional[PhysicsEngine] = None
        self.renderer_3d: Optional[Renderer3D] = None
        
        # アプリケーション状態
        self.is_running = False
        self.simulation_timer: Optional[QTimer] = None
        
        # ロギング設定
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """ロギングシステムの設定"""
        logger = logging.getLogger('AstroSim')
        
        if not logger.handlers:
            # ログディレクトリの作成
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # ファイルハンドラー
            file_handler = logging.FileHandler(
                log_dir / "astrosim.log", 
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # コンソールハンドラー
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # フォーマッター
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def initialize(self) -> bool:
        """
        アプリケーションの初期化
        
        Returns:
            初期化成功の場合True
        """
        try:
            self.logger.info("AstroSimアプリケーション初期化開始")
            
            # 1. Qt アプリケーションの初期化
            if not self._initialize_qt_application():
                return False
            
            # 2. データシステムの初期化
            if not self._initialize_data_system():
                return False
            
            # 3. シミュレーションシステムの初期化
            if not self._initialize_simulation_system():
                return False
            
            # 4. 3D可視化システムの初期化
            if not self._initialize_visualization_system():
                return False
            
            # 5. UIシステムの初期化
            if not self._initialize_ui_system():
                return False
            
            # 6. システム統合とイベント接続
            if not self._connect_systems():
                return False
            
            self.logger.info("AstroSimアプリケーション初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"初期化エラー: {e}")
            self._show_error_dialog("初期化エラー", f"アプリケーションの初期化に失敗しました:\n{e}")
            return False
    
    def _initialize_qt_application(self) -> bool:
        """Qt アプリケーションの初期化"""
        try:
            self.app = QApplication(sys.argv)
            
            # アプリケーション情報設定
            self.app.setApplicationName("AstroSim")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("AstroSim Development")
            
            # ハイDPI対応（Qt6では自動的に有効化されるため、設定不要）
            # Qt6では以下の属性は削除されました：
            # - AA_EnableHighDpiScaling（自動的に有効）
            # - AA_UseHighDpiPixmaps（自動的に有効）
            
            self.logger.info("Qt アプリケーション初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"Qt アプリケーション初期化エラー: {e}")
            return False
    
    def _initialize_data_system(self) -> bool:
        """データシステムの初期化"""
        try:
            # データローダーの初期化
            self.data_loader = DataLoader()
            self.logger.info("DataLoader 初期化完了")
            
            # 設定管理の初期化
            self.config_manager = self.data_loader.load_config()
            self.logger.info("ConfigManager 初期化完了")
            
            # 太陽系データの読み込み
            self.solar_system = self.data_loader.load_default_solar_system()
            self.logger.info(f"太陽系データ読み込み完了: {self.solar_system.get_planet_count()}惑星")
            
            return True
            
        except Exception as e:
            self.logger.error(f"データシステム初期化エラー: {e}")
            return False
    
    def _initialize_simulation_system(self) -> bool:
        """シミュレーションシステムの初期化"""
        try:
            # 時間管理の初期化
            self.time_manager = TimeManager()
            
            # J2000.0エポックに設定
            self.time_manager.current_julian_date = 2451545.0
            
            # 物理エンジンの初期化
            self.physics_engine = PhysicsEngine()
            
            # 初期位置の計算
            self.solar_system.update_all_positions(self.time_manager.current_julian_date)
            
            self.logger.info("シミュレーションシステム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"シミュレーションシステム初期化エラー: {e}")
            return False
    
    def _initialize_visualization_system(self) -> bool:
        """3D可視化システムの初期化"""
        try:
            # 3Dレンダラーの初期化は後でメインウィンドウ内で行う
            self.logger.info("可視化システム初期化準備完了")
            return True
            
        except Exception as e:
            self.logger.error(f"可視化システム初期化エラー: {e}")
            return False
    
    def _initialize_ui_system(self) -> bool:
        """UIシステムの初期化"""
        try:
            # メインウィンドウの作成
            self.main_window = MainWindow(
                config_manager=self.config_manager,
                solar_system=self.solar_system,
                time_manager=self.time_manager
            )
            
            # ウィンドウ設定の適用
            self._apply_window_settings()
            
            self.logger.info("UIシステム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"UIシステム初期化エラー: {e}")
            return False
    
    def _connect_systems(self) -> bool:
        """システム間の接続とイベント設定"""
        try:
            # シミュレーションタイマーの設定
            self.simulation_timer = QTimer()
            self.simulation_timer.timeout.connect(self._update_simulation)
            
            # 初期フレームレート設定（60 FPS）
            fps = self.config_manager.get("simulation.fps", 60)
            self.simulation_timer.setInterval(1000 // fps)
            
            # 時間管理コールバックの設定
            self.time_manager.add_time_change_callback(self._on_time_changed)
            
            self.logger.info("システム統合完了")
            return True
            
        except Exception as e:
            self.logger.error(f"システム統合エラー: {e}")
            return False
    
    def _apply_window_settings(self) -> None:
        """ウィンドウ設定の適用"""
        if not self.main_window or not self.config_manager:
            return
        
        try:
            # ウィンドウサイズ
            width = self.config_manager.get("window.width", 1600)
            height = self.config_manager.get("window.height", 1000)
            self.main_window.resize(width, height)
            
            # ウィンドウ位置
            if self.config_manager.get("window.remember_position", True):
                x = self.config_manager.get("window.x", 100)
                y = self.config_manager.get("window.y", 100)
                self.main_window.move(x, y)
            
            # 最大化状態
            if self.config_manager.get("window.maximized", False):
                self.main_window.showMaximized()
            
            self.logger.info("ウィンドウ設定適用完了")
            
        except Exception as e:
            self.logger.warning(f"ウィンドウ設定適用エラー: {e}")
    
    def _update_simulation(self) -> None:
        """シミュレーション更新（タイマーコールバック）"""
        try:
            if not self.time_manager.is_paused:
                # 実時間での経過時間を計算（秒）
                dt = self.simulation_timer.interval() / 1000.0
                
                # 時間を進める
                self.time_manager.update(dt)
                
                # 太陽系の位置を更新
                self.solar_system.update_all_positions(self.time_manager.current_julian_date)
                
                # 3D表示を更新
                if self.main_window:
                    self.main_window.update_3d_view()
                    
        except Exception as e:
            self.logger.error(f"シミュレーション更新エラー: {e}")
    
    def _on_time_changed(self, julian_date: float) -> None:
        """時間変更時のコールバック"""
        try:
            # UIの時間表示を更新
            if self.main_window:
                self.main_window.update_time_display()
                
        except Exception as e:
            self.logger.error(f"時間変更コールバックエラー: {e}")
    
    def start_simulation(self) -> None:
        """シミュレーション開始"""
        if self.simulation_timer and not self.simulation_timer.isActive():
            self.simulation_timer.start()
            self.is_running = True
            self.logger.info("シミュレーション開始")
    
    def pause_simulation(self) -> None:
        """シミュレーション一時停止"""
        if self.time_manager:
            self.time_manager.pause()
            self.logger.info("シミュレーション一時停止")
    
    def resume_simulation(self) -> None:
        """シミュレーション再開"""
        if self.time_manager:
            self.time_manager.resume()
            self.logger.info("シミュレーション再開")
    
    def stop_simulation(self) -> None:
        """シミュレーション停止"""
        if self.simulation_timer and self.simulation_timer.isActive():
            self.simulation_timer.stop()
            self.is_running = False
            self.logger.info("シミュレーション停止")
    
    def run(self) -> int:
        """
        アプリケーションのメインループ実行
        
        Returns:
            終了コード
        """
        try:
            if not self.app or not self.main_window:
                self.logger.error("アプリケーションが初期化されていません")
                return 1
            
            # メインウィンドウを表示
            self.main_window.show()
            
            # シミュレーション開始
            self.start_simulation()
            
            self.logger.info("アプリケーション開始")
            
            # メインループ実行
            return self.app.exec()
            
        except Exception as e:
            self.logger.error(f"アプリケーション実行エラー: {e}")
            self._show_error_dialog("実行エラー", f"アプリケーションの実行中にエラーが発生しました:\n{e}")
            return 1
    
    def shutdown(self) -> None:
        """アプリケーションの終了処理"""
        try:
            self.logger.info("アプリケーション終了処理開始")
            
            # シミュレーション停止
            self.stop_simulation()
            
            # 設定の保存
            if self.config_manager and self.main_window:
                self._save_window_settings()
                self.config_manager.save()
            
            # ログ終了
            self.logger.info("AstroSimアプリケーション終了")
            
        except Exception as e:
            print(f"終了処理エラー: {e}")
    
    def _save_window_settings(self) -> None:
        """ウィンドウ設定の保存"""
        try:
            if not self.main_window or not self.config_manager:
                return
            
            # ウィンドウサイズ
            size = self.main_window.size()
            self.config_manager.set("window.width", size.width())
            self.config_manager.set("window.height", size.height())
            
            # ウィンドウ位置
            pos = self.main_window.pos()
            self.config_manager.set("window.x", pos.x())
            self.config_manager.set("window.y", pos.y())
            
            # 最大化状態
            self.config_manager.set("window.maximized", self.main_window.isMaximized())
            
            self.logger.info("ウィンドウ設定保存完了")
            
        except Exception as e:
            self.logger.warning(f"ウィンドウ設定保存エラー: {e}")
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """エラーダイアログの表示"""
        try:
            if self.app:
                QMessageBox.critical(None, title, message)
            else:
                print(f"ERROR: {title} - {message}")
        except Exception:
            print(f"ERROR: {title} - {message}")


def main() -> int:
    """
    メインエントリーポイント
    
    Returns:
        終了コード
    """
    # 引数処理
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print("AstroSim - 太陽系惑星軌道シミュレーション")
            print("使用法: python main.py [オプション]")
            print("オプション:")
            print("  -h, --help     このヘルプを表示")
            print("  --version      バージョン情報を表示")
            return 0
        
        if "--version" in sys.argv:
            print("AstroSim v1.0.0")
            print("Python太陽系惑星軌道シミュレーション")
            return 0
    
    # アプリケーション実行
    app = AstroSimApplication()
    
    try:
        # 初期化
        if not app.initialize():
            print("アプリケーションの初期化に失敗しました。")
            return 1
        
        # 実行
        return app.run()
        
    except KeyboardInterrupt:
        print("\nユーザーによる中断")
        return 0
    except Exception as e:
        print(f"予期しないエラー: {e}")
        traceback.print_exc()
        return 1
    finally:
        app.shutdown()


if __name__ == "__main__":
    sys.exit(main())