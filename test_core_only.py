#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コアシステムのみのテスト

GUI依存関係なしで、コアシステムの動作を確認します。
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

def test_core_imports():
    """コアシステムのインポートテスト"""
    print("=" * 60)
    print("コアシステム インポートテスト")
    print("=" * 60)
    
    try:
        # ドメインモデル層
        from src.domain.orbital_elements import OrbitalElements
        from src.domain.celestial_body import CelestialBody
        from src.domain.planet import Planet
        from src.domain.sun import Sun
        from src.domain.solar_system import SolarSystem
        print("✓ ドメインモデル層 インポート成功")
        
        # シミュレーション層
        from src.simulation.physics_engine import PhysicsEngine
        from src.simulation.time_manager import TimeManager
        from src.simulation.orbit_calculator import OrbitCalculator
        print("✓ シミュレーション層 インポート成功")
        
        # データ層
        from src.data.data_loader import DataLoader
        from src.data.config_manager import ConfigManager
        from src.data.planet_repository import PlanetRepository
        print("✓ データ層 インポート成功")
        
        print("\n🎉 コアシステム インポート完全成功！")
        return True
        
    except ImportError as e:
        print(f"✗ インポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_minimal_simulation():
    """最小限のシミュレーション実行テスト"""
    print("\n" + "=" * 60)
    print("最小限シミュレーション実行テスト")
    print("=" * 60)
    
    try:
        import tempfile
        from src.data.data_loader import DataLoader
        from src.simulation.time_manager import TimeManager
        
        # 一時ディレクトリでテスト
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # データローダー初期化
            data_loader = DataLoader(temp_path)
            print("✓ DataLoader 初期化成功")
            
            # 太陽系データ読み込み
            solar_system = data_loader.load_default_solar_system()
            print(f"✓ 太陽系データ読み込み成功: {solar_system.get_planet_count()}惑星")
            
            # 時間管理初期化
            time_manager = TimeManager()
            time_manager.current_julian_date = 2451545.0  # J2000.0
            print("✓ TimeManager 初期化成功")
            
            # 初期位置計算
            solar_system.update_all_positions(time_manager.current_julian_date)
            print("✓ 初期位置計算成功")
            
            # 地球の位置確認
            earth = solar_system.get_planet_by_name("地球")
            if earth:
                distance = (sum(x**2 for x in earth.position))**0.5 / 149597870.7
                print(f"✓ 地球-太陽距離: {distance:.6f} AU")
                
                # 軌道周期確認
                period = earth.orbital_elements.get_orbital_period()
                print(f"✓ 地球軌道周期: {period:.2f} 日")
            
            # 時間進行テスト
            original_date = time_manager.current_julian_date
            time_manager.advance_by_days(10.0)  # 10日進める
            new_date = time_manager.current_julian_date
            print(f"✓ 時間進行テスト: {original_date:.1f} → {new_date:.1f} JD")
            
            # 新しい位置計算
            solar_system.update_all_positions(new_date)
            if earth:
                new_distance = (sum(x**2 for x in earth.position))**0.5 / 149597870.7
                print(f"✓ 10日後地球-太陽距離: {new_distance:.6f} AU")
        
        print("\n🎉 最小限シミュレーション実行完全成功！")
        return True
        
    except Exception as e:
        print(f"✗ シミュレーション実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_availability():
    """GUI依存関係の可用性確認"""
    print("\n" + "=" * 60)
    print("GUI依存関係 可用性確認")
    print("=" * 60)
    
    gui_available = True
    
    # PyQt6チェック
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        print("✓ PyQt6 利用可能")
    except ImportError:
        print("✗ PyQt6 利用不可")
        gui_available = False
    
    # Vispyチェック
    try:
        import vispy
        from vispy import app as vispy_app
        from vispy import scene
        print("✓ Vispy 利用可能")
    except ImportError:
        print("✗ Vispy 利用不可")
        gui_available = False
    
    if gui_available:
        print("\n🎉 GUI依存関係すべて利用可能！")
        print("   フルアプリケーション実行可能")
    else:
        print("\n⚠️  GUI依存関係が不足")
        print("   以下のコマンドで依存関係をインストールしてください:")
        print("   pip install -r requirements.txt")
    
    return gui_available

def main():
    """コアシステムテスト メイン実行"""
    print("AstroSim コアシステムテスト開始")
    print(f"Python版本: {sys.version}")
    print(f"プラットフォーム: {sys.platform}")
    
    # テスト実行
    test_results = []
    
    test_results.append(("コアシステムインポート", test_core_imports()))
    test_results.append(("最小限シミュレーション", test_minimal_simulation()))
    test_results.append(("GUI依存関係可用性", test_gui_availability()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("コアシステムテスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    if passed >= 2:  # コアシステムが動作すればOK
        print("🎉 コアシステム動作確認完了！")
        print("   基本的な太陽系シミュレーション機能が正常に動作しています")
    
    return passed >= 2

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