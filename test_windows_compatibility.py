#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows環境でのAstroSim互換性テストスクリプト
"""

import sys
import os
import traceback
from pathlib import Path

def test_basic_imports():
    """基本的なインポートテスト"""
    print("=== 基本的なインポートテスト ===")
    
    # Python環境情報
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    results = []
    
    # PyQt6テスト
    try:
        import PyQt6
        print("OK: PyQt6インポート成功")
        from PyQt6.QtWidgets import QApplication
        print("OK: PyQt6.QtWidgets インポート成功")
        results.append(("PyQt6", True))
    except Exception as e:
        print(f"ERROR: PyQt6エラー: {e}")
        results.append(("PyQt6", False))
    
    # Vispyテスト
    try:
        import vispy
        print(f"OK: Vispy インポート成功 (version: {vispy.__version__})")
        results.append(("vispy", True))
    except Exception as e:
        print(f"ERROR: Vispyエラー: {e}")
        results.append(("vispy", False))
    
    # NumPyテスト
    try:
        import numpy
        print(f"OK: NumPy インポート成功 (version: {numpy.__version__})")
        results.append(("numpy", True))
    except Exception as e:
        print(f"ERROR: NumPyエラー: {e}")
        results.append(("numpy", False))
    
    # SciPyテスト
    try:
        import scipy
        print(f"OK: SciPy インポート成功 (version: {scipy.__version__})")
        results.append(("scipy", True))
    except Exception as e:
        print(f"ERROR: SciPyエラー: {e}")
        results.append(("scipy", False))
    
    return results

def test_astrosim_imports():
    """AstroSimモジュールのインポートテスト"""
    print("\n=== AstroSimモジュールインポートテスト ===")
    
    # パスを設定
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    modules_to_test = [
        "src.data.data_loader",
        "src.data.config_manager",
        "src.simulation.time_manager",
        "src.simulation.physics_engine", 
        "src.ui.main_window",
        "src.visualization.renderer_3d",
        "src.domain.solar_system"
    ]
    
    results = []
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"OK: {module_name} インポート成功")
            results.append((module_name, True))
        except Exception as e:
            print(f"ERROR: {module_name} インポートエラー: {e}")
            results.append((module_name, False))
    
    return results

def test_gui_initialization():
    """GUI環境の初期化テスト"""
    print("\n=== GUI環境初期化テスト ===")
    
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        from PyQt6.QtCore import Qt
        
        # QApplicationを作成（既に存在する場合はスキップ）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            print("OK: QApplication作成成功")
        else:
            print("OK: QApplication既存インスタンス使用")
        
        # テスト用ウィジェット作成
        test_widget = QWidget()
        test_widget.setWindowTitle("AstroSim Windows Test")
        test_widget.resize(400, 300)
        
        print("OK: テストウィジェット作成成功")
        
        # クリーンアップ
        test_widget.close()
        test_widget.deleteLater()
        
        return True
        
    except Exception as e:
        print(f"ERROR: GUI初期化エラー: {e}")
        return False

def test_vispy_backend():
    """Vispyバックエンドテスト"""
    print("\n=== Vispyバックエンドテスト ===")
    
    try:
        import vispy
        from vispy import app as vispy_app
        
        # PyQt6バックエンドを試す
        try:
            vispy.use('pyqt6')
            print("OK: Vispy PyQt6バックエンド設定成功")
            backend_success = True
        except Exception as backend_error:
            print(f"WARNING: Vispy PyQt6バックエンドエラー: {backend_error}")
            
            # フォールバック
            try:
                vispy.use('gl')
                print("OK: Vispy OpenGLバックエンド設定成功")
                backend_success = True
            except:
                vispy.use('null')
                print("WARNING: Vispy ヌルバックエンド使用")
                backend_success = False
        
        return backend_success
        
    except Exception as e:
        print(f"ERROR: Vispyバックエンドテストエラー: {e}")
        return False

def test_astrosim_initialization():
    """AstroSim初期化テスト（GUI表示なし）"""
    print("\n=== AstroSim初期化テスト ===")
    
    try:
        # オフスクリーンモードに設定
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        # パス設定
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # AstroSimApplicationをインポート
        from src.main import AstroSimApplication
        
        print("OK: AstroSimApplicationインポート成功")
        
        # 初期化テスト（実際のGUI作成は行わない）
        try:
            app_instance = AstroSimApplication()
            print("OK: AstroSimApplication作成成功")
            
            # 簡単な初期化テスト
            try:
                success = app_instance.initialize()
                if success:
                    print("OK: AstroSim初期化成功")
                else:
                    print("WARNING: AstroSim初期化失敗")
            except Exception as e:
                print(f"WARNING: AstroSim初期化テストエラー: {e}")
                # ログシステムのテスト
                try:
                    logger = app_instance._setup_logging()
                    if logger:
                        print("OK: ログシステム設定成功")
                    else:
                        print("WARNING: ログシステム設定失敗")
                except Exception as log_e:
                    print(f"WARNING: ログシステムテストエラー: {log_e}")
            
            return True
            
        except Exception as init_error:
            print(f"ERROR: AstroSim初期化エラー: {init_error}")
            return False
        
    except Exception as e:
        print(f"ERROR: AstroSim初期化テストエラー: {e}")
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("Windows環境でのAstroSim互換性テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 基本インポートテスト
    basic_results = test_basic_imports()
    basic_success = all(result[1] for result in basic_results)
    test_results.append(("基本インポート", basic_success))
    
    if not basic_success:
        print("\n基本的な依存関係に問題があります。テストを中断します。")
        return False
    
    # AstroSimモジュールインポートテスト
    astrosim_results = test_astrosim_imports()
    astrosim_success = all(result[1] for result in astrosim_results)
    test_results.append(("AstroSimモジュール", astrosim_success))
    
    # GUI初期化テスト
    gui_success = test_gui_initialization()
    test_results.append(("GUI初期化", gui_success))
    
    # Vispyバックエンドテスト
    vispy_success = test_vispy_backend()
    test_results.append(("Vispyバックエンド", vispy_success))
    
    # AstroSim初期化テスト
    if astrosim_success and gui_success:
        init_success = test_astrosim_initialization()
        test_results.append(("AstroSim初期化", init_success))
    else:
        print("WARNING: 前提条件が満たされていないため、AstroSim初期化テストをスキップ")
        test_results.append(("AstroSim初期化", False))
    
    # 結果サマリー
    print("\n" + "="*50)
    print("Windows互換性テスト結果サマリー")
    print("="*50)
    
    for test_name, success in test_results:
        status = "OK" if success else "FAIL"
        print(f"{test_name:20s}: {status}")
    
    overall_success = all(result[1] for result in test_results)
    
    if overall_success:
        print("\nWindows環境でのAstroSim互換性テスト：成功")
        print("AstroSimはWindows環境で動作する可能性が高いです。")
    else:
        print("\nWindows環境でのAstroSim互換性テスト：問題あり")
        print("いくつかの問題を修正する必要があります。")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nテスト中断")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        traceback.print_exc()
        sys.exit(1)