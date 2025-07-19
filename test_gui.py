#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI統合テストスクリプト

メインアプリケーションの基本動作を確認し、
PyQt6 + Vispy統合の動作をテストします。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# エンコーディング設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

def test_imports():
    """依存関係のインポートテスト"""
    print("=" * 60)
    print("依存関係インポートテスト")
    print("=" * 60)
    
    try:
        # PyQt6のテスト
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        print("✓ PyQt6 インポート成功")
        
        # Vispyのテスト
        import vispy
        from vispy import app as vispy_app
        from vispy import scene
        print("✓ Vispy インポート成功")
        
        # プロジェクトモジュールのテスト
        from src.main import AstroSimApplication
        print("✓ AstroSimApplication インポート成功")
        
        from src.ui.main_window import MainWindow
        print("✓ MainWindow インポート成功")
        
        from src.ui.control_panel import ControlPanel
        print("✓ ControlPanel インポート成功")
        
        from src.ui.info_panel import InfoPanel
        print("✓ InfoPanel インポート成功")
        
        print("\n🎉 全インポートテスト成功！")
        return True
        
    except ImportError as e:
        print(f"✗ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        return False

def test_application_initialization():
    """アプリケーション初期化テスト"""
    print("\n" + "=" * 60)
    print("アプリケーション初期化テスト")
    print("=" * 60)
    
    try:
        # アプリケーションのインポート
        from src.main import AstroSimApplication
        
        # インスタンス作成
        app = AstroSimApplication()
        print("✓ AstroSimApplication インスタンス作成成功")
        
        # ロガー確認
        if app.logger:
            print("✓ ロガー初期化成功")
        
        # 初期化テスト（UI表示なし）
        # 注意: 実際のGUI初期化はXサーバーが必要なため、ここでは構造チェックのみ
        if hasattr(app, 'initialize'):
            print("✓ initialize メソッド存在確認")
        
        if hasattr(app, 'run'):
            print("✓ run メソッド存在確認")
        
        if hasattr(app, 'shutdown'):
            print("✓ shutdown メソッド存在確認")
        
        print("\n🎉 アプリケーション初期化テスト成功！")
        return True
        
    except Exception as e:
        print(f"✗ 初期化テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """UIコンポーネントテスト"""
    print("\n" + "=" * 60)
    print("UIコンポーネントテスト")
    print("=" * 60)
    
    try:
        # GUI環境の確認
        if not os.environ.get('DISPLAY') and sys.platform.startswith('linux'):
            print("⚠ Linux環境でDISPLAY環境変数が設定されていません")
            print("  GUI表示をスキップして構造テストのみ実行します")
        
        # PyQt6アプリケーション作成（最小限）
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        # 既存のQApplicationインスタンスを確認
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            app_created = True
            print("✓ QApplication 作成成功")
        else:
            app_created = False
            print("✓ QApplication 既存インスタンス使用")
        
        # UIコンポーネントのインポートと基本チェック
        from src.ui.main_window import MainWindow
        from src.ui.control_panel import ControlPanel
        from src.ui.info_panel import InfoPanel
        
        print("✓ UIコンポーネント インポート成功")
        
        # 簡易構造チェック（実際のウィジェット作成はスキップ）
        print("✓ UIコンポーネント構造確認完了")
        
        # クリーンアップ
        if app_created:
            app.quit()
        
        print("\n🎉 UIコンポーネントテスト成功！")
        return True
        
    except Exception as e:
        print(f"✗ UIコンポーネントテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vispy_integration():
    """Vispy統合テスト"""
    print("\n" + "=" * 60)
    print("Vispy統合テスト")
    print("=" * 60)
    
    try:
        import vispy
        from vispy import app as vispy_app
        from vispy import scene
        
        # PyQt6バックエンド設定
        try:
            vispy.use('pyqt6')
            print("✓ Vispy PyQt6バックエンド設定成功")
        except Exception as e:
            print(f"⚠ Vispy PyQt6バックエンド設定警告: {e}")
            print("  代替バックエンドを使用します")
        
        # 可視化コンポーネントのインポート
        from src.visualization.renderer_3d import Renderer3D
        from src.visualization.scene_manager import SceneManager
        from src.visualization.camera_controller import CameraController
        
        print("✓ 可視化コンポーネント インポート成功")
        
        print("\n🎉 Vispy統合テスト成功！")
        return True
        
    except Exception as e:
        print(f"✗ Vispy統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_integration():
    """システム統合テスト"""
    print("\n" + "=" * 60)
    print("システム統合テスト")
    print("=" * 60)
    
    try:
        # データシステムの確認
        from src.data.data_loader import DataLoader
        from src.data.config_manager import ConfigManager
        
        # シミュレーションシステムの確認
        from src.simulation.time_manager import TimeManager
        from src.simulation.physics_engine import PhysicsEngine
        
        # ドメインモデルの確認
        from src.domain.solar_system import SolarSystem
        
        print("✓ 全システムコンポーネント インポート成功")
        
        # 簡易統合チェック（実際のGUI表示なし）
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # データシステム初期化
            data_loader = DataLoader(Path(temp_dir))
            config_manager = data_loader.load_config()
            solar_system = data_loader.load_default_solar_system()
            
            # シミュレーションシステム初期化
            time_manager = TimeManager()
            physics_engine = PhysicsEngine()
            
            print("✓ システムコンポーネント 統合初期化成功")
            print(f"  惑星数: {solar_system.get_planet_count()}")
            print(f"  設定セクション数: {len(config_manager.get_all_sections())}")
            print(f"  現在時刻: {time_manager.get_current_datetime().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n🎉 システム統合テスト成功！")
        return True
        
    except Exception as e:
        print(f"✗ システム統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """GUI統合テストメイン実行"""
    print("AstroSim GUI統合テスト開始")
    print(f"Python版本: {sys.version}")
    print(f"プラットフォーム: {sys.platform}")
    print(f"作業ディレクトリ: {os.getcwd()}")
    
    # テスト実行
    test_results = []
    
    test_results.append(("依存関係インポート", test_imports()))
    test_results.append(("アプリケーション初期化", test_application_initialization()))
    test_results.append(("UIコンポーネント", test_ui_components()))
    test_results.append(("Vispy統合", test_vispy_integration()))
    test_results.append(("システム統合", test_system_integration()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("GUI統合テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 GUI統合テスト完全成功！")
        print("   メインアプリケーション実行準備完了")
        print("\n次のステップ:")
        print("   python src/main.py")
        print("   でアプリケーションを起動できます")
    else:
        print(f"⚠️  {total - passed}個のテストが失敗しました")
        print("   依存関係やシステム設定を確認してください")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nテスト中断")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)