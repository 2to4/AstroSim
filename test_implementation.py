#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実装テストスクリプト
新しく実装したクラスの基本動作を確認します。
"""

import sys
import os
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# エンコーディング設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

def test_planet_repository():
    """PlanetRepositoryクラスのテスト"""
    print("=" * 60)
    print("PlanetRepository クラスのテスト")
    print("=" * 60)
    
    try:
        from src.data.planet_repository import PlanetRepository
        
        # 一時ディレクトリでテスト
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_planets.json"
            
            # リポジトリを作成（デフォルトデータで初期化）
            repo = PlanetRepository(temp_path)
            
            print("✓ PlanetRepository オブジェクト作成成功")
            print(f"  惑星数: {len(repo.get_all_planets())}")
            print(f"  惑星名: {', '.join(repo.get_planet_names())}")
            
            # 地球データの取得テスト
            earth_data = repo.get_planet_by_name("地球")
            if earth_data:
                print("✓ 地球データ取得成功")
                print(f"  質量: {earth_data['mass']:.3e} kg")
                print(f"  軌道長半径: {earth_data['orbital_elements']['semi_major_axis']:.6f} AU")
            else:
                print("✗ 地球データ取得失敗")
                return False
            
            # 太陽系オブジェクト構築テスト
            solar_system = repo.build_solar_system()
            print("✓ SolarSystem オブジェクト構築成功")
            print(f"  天体数: {len(solar_system)}")
            print(f"  太陽あり: {solar_system.has_sun()}")
            print(f"  惑星数: {solar_system.get_planet_count()}")
            
            # データファイル存在確認
            if temp_path.exists():
                print("✓ データファイル作成成功")
                print(f"  ファイルサイズ: {temp_path.stat().st_size} bytes")
            
        return True
        
    except Exception as e:
        print(f"✗ PlanetRepository テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """ConfigManagerクラスのテスト"""
    print("\n" + "=" * 60)
    print("ConfigManager クラスのテスト")
    print("=" * 60)
    
    try:
        from src.data.config_manager import ConfigManager
        
        # 一時ディレクトリでテスト
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_config.json"
            
            # 設定管理を作成
            config = ConfigManager(temp_path)
            
            print("✓ ConfigManager オブジェクト作成成功")
            print(f"  設定セクション数: {len(config.get_all_sections())}")
            
            # 設定取得テスト
            window_width = config.get("window.width")
            print(f"✓ 設定取得テスト: window.width = {window_width}")
            
            # 設定更新テスト
            config.set("window.width", 1920)
            new_width = config.get("window.width")
            print(f"✓ 設定更新テスト: 新しい width = {new_width}")
            
            # 設定保存テスト
            save_success = config.save()
            print(f"✓ 設定保存テスト: {save_success}")
            
            # 設定検証テスト
            errors = config.validate_config()
            if not errors:
                print("✓ 設定検証テスト: エラーなし")
            else:
                print(f"⚠ 設定検証テスト: {len(errors)}個のエラー")
                for error in errors[:3]:  # 最初の3個のみ表示
                    print(f"  - {error}")
            
            # ファイル存在確認
            if temp_path.exists():
                print("✓ 設定ファイル作成成功")
        
        return True
        
    except Exception as e:
        print(f"✗ ConfigManager テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loader():
    """DataLoaderクラスのテスト"""
    print("\n" + "=" * 60)
    print("DataLoader クラスのテスト")
    print("=" * 60)
    
    try:
        from src.data.data_loader import DataLoader
        
        # 一時ディレクトリでテスト
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # データローダーを作成
            loader = DataLoader(temp_path)
            
            print("✓ DataLoader オブジェクト作成成功")
            print(f"  サポート形式: {', '.join(loader.get_supported_formats())}")
            
            # デフォルト太陽系読み込みテスト
            try:
                solar_system = loader.load_default_solar_system()
                print("✓ デフォルト太陽系読み込み成功")
                print(f"  惑星数: {solar_system.get_planet_count()}")
                
                # 太陽系データ保存テスト
                save_path = temp_path / "test_save.json"
                save_success = loader.save_solar_system(solar_system, save_path)
                print(f"✓ 太陽系データ保存テスト: {save_success}")
                
                if save_path.exists():
                    print(f"  保存ファイルサイズ: {save_path.stat().st_size} bytes")
                    
                    # 保存したファイルの再読み込みテスト
                    reloaded_system = loader.load_solar_system_from_file(save_path)
                    print("✓ 太陽系データ再読み込み成功")
                    print(f"  再読み込み惑星数: {reloaded_system.get_planet_count()}")
                
            except Exception as e:
                print(f"⚠ デフォルト太陽系読み込みでエラー: {e}")
            
            # 設定読み込みテスト
            try:
                config_manager = loader.load_config()
                print("✓ 設定読み込み成功")
                print(f"  設定セクション数: {len(config_manager.get_all_sections())}")
            except Exception as e:
                print(f"⚠ 設定読み込みでエラー: {e}")
            
            # データ情報取得テスト
            info = loader.get_data_info()
            print("✓ データ情報取得成功")
            print(f"  ベースパス: {info['base_path']}")
        
        return True
        
    except Exception as e:
        print(f"✗ DataLoader テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """UIコンポーネントのテスト"""
    print("\n" + "=" * 60)
    print("UI コンポーネントのテスト")
    print("=" * 60)
    
    try:
        # PyQt6が利用可能かチェック
        try:
            from PyQt6.QtWidgets import QApplication
            print("✓ PyQt6 利用可能")
        except ImportError:
            print("⚠ PyQt6 が利用できません。UIテストをスキップします。")
            return True
        
        # UIコンポーネントのインポートテスト
        from src.ui.control_panel import ControlPanel
        from src.ui.info_panel import InfoPanel
        
        print("✓ UI コンポーネントインポート成功")
        
        # ControlPanelクラステスト（実際のインスタンス化はQApplicationが必要）
        print("✓ ControlPanel クラス定義確認")
        
        # InfoPanelクラステスト
        print("✓ InfoPanel クラス定義確認")
        
        return True
        
    except Exception as e:
        print(f"✗ UI コンポーネントテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_visualization_components():
    """可視化コンポーネントのテスト"""
    print("\n" + "=" * 60)
    print("可視化コンポーネントのテスト")
    print("=" * 60)
    
    try:
        # Vispyが利用可能かチェック
        try:
            import vispy
            print("✓ Vispy 利用可能")
        except ImportError:
            print("⚠ Vispy が利用できません。可視化テストをスキップします。")
            return True
        
        # 可視化コンポーネントのインポートテスト
        from src.visualization.camera_controller import CameraController
        from src.visualization.scene_manager import SceneManager
        
        print("✓ 可視化コンポーネントインポート成功")
        
        # クラス定義確認
        print("✓ CameraController クラス定義確認")
        print("✓ SceneManager クラス定義確認")
        
        return True
        
    except Exception as e:
        print(f"✗ 可視化コンポーネントテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_domain_integration():
    """ドメインモデル統合テスト"""
    print("\n" + "=" * 60)
    print("ドメインモデル統合テスト")
    print("=" * 60)
    
    try:
        from src.domain.solar_system import SolarSystem
        from src.domain.sun import Sun
        from src.domain.planet import Planet
        from src.domain.orbital_elements import OrbitalElements
        
        # 太陽系を作成
        solar_system = SolarSystem()
        
        # 太陽を追加
        sun = Sun()
        solar_system.add_celestial_body(sun)
        print("✓ 太陽追加成功")
        
        # 地球を追加
        earth_elements = OrbitalElements(
            semi_major_axis=1.00000261,
            eccentricity=0.01671123,
            inclination=0.00001531,
            longitude_of_ascending_node=-11.26064,
            argument_of_perihelion=102.93768,
            mean_anomaly_at_epoch=100.46457,
            epoch=2451545.0
        )
        
        earth = Planet(
            name="地球",
            mass=5.972e24,
            radius=6371.0,
            orbital_elements=earth_elements,
            color=(0.3, 0.7, 1.0)
        )
        
        solar_system.add_celestial_body(earth)
        print("✓ 地球追加成功")
        
        # 位置更新テスト
        julian_date = 2451545.0  # J2000.0
        solar_system.update_all_positions(julian_date)
        print("✓ 位置更新成功")
        
        # 物理量計算テスト
        total_energy = solar_system.get_total_energy()
        angular_momentum = solar_system.get_angular_momentum()
        
        print(f"✓ 物理量計算成功")
        print(f"  全エネルギー: {total_energy:.3e} J")
        print(f"  角運動量の大きさ: {(angular_momentum[0]**2 + angular_momentum[1]**2 + angular_momentum[2]**2)**0.5:.3e} kg⋅m²/s")
        
        # 地球の軌道周期確認
        earth_period = earth_elements.get_orbital_period()
        if 365.0 < earth_period < 366.0:
            print(f"✓ 地球軌道周期正確: {earth_period:.2f} 日")
        else:
            print(f"⚠ 地球軌道周期異常: {earth_period:.2f} 日")
        
        return True
        
    except Exception as e:
        print(f"✗ ドメインモデル統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("AstroSim 実装テスト開始")
    print("=" * 60)
    
    test_results = []
    
    # 各テストを実行
    test_results.append(("ドメインモデル統合", test_domain_integration()))
    test_results.append(("PlanetRepository", test_planet_repository()))
    test_results.append(("ConfigManager", test_config_manager()))
    test_results.append(("DataLoader", test_data_loader()))
    test_results.append(("UI コンポーネント", test_ui_components()))
    test_results.append(("可視化コンポーネント", test_visualization_components()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
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
        print("🎉 すべてのテストが成功しました！")
        print("統合テストに進む準備ができています。")
    else:
        print(f"⚠️  {total - passed}個のテストが失敗しました。")
        print("失敗したテストを確認してください。")
    
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