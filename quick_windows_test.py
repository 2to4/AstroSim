#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows環境でのAstroSim実機動作テスト（短時間実行）
"""

import sys
import os
from pathlib import Path
import time

def main():
    """短時間でのAstroSim実機テスト"""
    print("Windows環境でのAstroSim実機テスト開始")
    
    # パス設定
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # GUIモードでAstroSimを起動（5秒後に自動終了）
        from src.main import AstroSimApplication
        
        print("AstroSimアプリケーションを作成中...")
        app_instance = AstroSimApplication()
        
        print("アプリケーションを初期化中...")
        if app_instance.initialize():
            print("初期化成功！")
            
            # 短時間実行（5秒間）
            print("AstroSimを5秒間実行します...")
            
            # タイマーで自動終了
            from PyQt6.QtCore import QTimer
            if app_instance.app:
                exit_timer = QTimer()
                exit_timer.timeout.connect(app_instance.app.quit)
                exit_timer.start(5000)  # 5秒後に終了
                
                print("GUI表示中...")
                start_time = time.time()
                
                # メインウィンドウを表示
                if app_instance.main_window:
                    app_instance.main_window.show()
                
                # メインループ実行
                exit_code = app_instance.app.exec()
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"実行完了！実行時間: {duration:.2f}秒")
                print(f"終了コード: {exit_code}")
                
                if exit_code == 0:
                    print("SUCCESS: AstroSimはWindows環境で正常に動作しました！")
                    return True
                else:
                    print("WARNING: アプリケーションは動作しましたが、正常終了しませんでした")
                    return False
            else:
                print("ERROR: アプリケーションの作成に失敗")
                return False
        else:
            print("ERROR: アプリケーションの初期化に失敗")
            return False
            
    except Exception as e:
        print(f"ERROR: 実機テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nWindows動作確認: 成功")
            print("AstroSimはWindows環境で動作します！")
        else:
            print("\nWindows動作確認: 問題あり")
            print("一部の機能に制限があります")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nテスト中断")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)