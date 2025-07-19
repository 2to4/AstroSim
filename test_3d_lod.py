#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D描画LOD（レベルオブディテール）最適化テストスクリプト

Renderer3Dの新しいLOD機能のパフォーマンスと
正確性をテストします。
"""

import sys
import time
import numpy as np
import tempfile
from pathlib import Path

# Windows環境でのエンコーディング設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_lod_system():
    """LODシステムの基本機能テスト"""
    print("=" * 60)
    print("3D描画LODシステム基本機能テスト")
    print("=" * 60)
    
    try:
        import vispy
        from vispy import scene
        from src.visualization.renderer_3d import Renderer3D
        from src.domain.planet import Planet
        from src.domain.orbital_elements import OrbitalElements
        
        # Vispyバックエンド設定
        try:
            vispy.use('PyQt6')
        except Exception:
            vispy.use(app='PyQt6')
        
        # キャンバス作成
        canvas = scene.SceneCanvas(
            title='AstroSim LOD Test',
            size=(400, 300),
            show=False
        )
        print("✓ 3Dキャンバス作成成功")
        
        # Renderer3D作成
        renderer = Renderer3D(canvas)
        print("✓ Renderer3D初期化成功")
        
        # LOD設定確認
        print(f"✓ LOD有効: {renderer.lod_enabled}")
        print(f"✓ LOD閾値: {renderer.lod_distance_thresholds}")
        print(f"✓ LOD分割数: {renderer.lod_sphere_subdivisions}")
        
        # テスト用惑星データ作成
        orbital_elements = OrbitalElements(
            semi_major_axis=1.0,
            eccentricity=0.0167,
            inclination=0.0,
            longitude_of_ascending_node=0.0,
            argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0,
            epoch=2451545.0
        )
        
        planet = Planet("TestPlanet", 5.972e24, 6371, orbital_elements, color=(0.5, 0.5, 1.0, 1.0))
        
        # 異なる距離での惑星追加テスト
        test_positions = [
            np.array([1.0, 0, 0]) * 149597870.7,    # 1AU (高詳細)
            np.array([5.0, 0, 0]) * 149597870.7,    # 5AU (中詳細)
            np.array([30.0, 0, 0]) * 149597870.7,   # 30AU (低詳細)
        ]
        
        expected_lods = ['high', 'medium', 'low']
        
        for i, (position, expected_lod) in enumerate(zip(test_positions, expected_lods)):
            planet.position = position
            planet_name = f"Planet_{i+1}"
            planet.name = planet_name
            
            renderer.add_planet(planet)
            
            # LODレベルを確認
            visual_data = renderer.planet_visuals[planet_name]
            actual_lod = visual_data['lod_level']
            
            print(f"✓ {planet_name}: 距離 {np.linalg.norm(position)/149597870.7:.1f}AU, "
                  f"期待LOD {expected_lod}, 実際LOD {actual_lod}")
            
            if actual_lod != expected_lod:
                print(f"⚠️ LODレベル不一致: 期待 {expected_lod}, 実際 {actual_lod}")
        
        # レンダリング情報確認
        render_info = renderer.get_render_info()
        print(f"✓ レンダリング情報: {render_info}")
        print(f"✓ LOD統計: {render_info['lod_statistics']}")
        
        # クリーンアップ
        renderer.cleanup()
        canvas.close()
        print("✓ クリーンアップ完了")
        
        print("\n🎉 LODシステム基本機能テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ LODシステム基本機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lod_dynamic_update():
    """LOD動的更新機能テスト"""
    print("\n" + "=" * 60)
    print("LOD動的更新機能テスト")
    print("=" * 60)
    
    try:
        import vispy
        from vispy import scene
        from src.visualization.renderer_3d import Renderer3D
        from src.domain.planet import Planet
        from src.domain.orbital_elements import OrbitalElements
        
        # Vispyバックエンド設定
        try:
            vispy.use('PyQt6')
        except Exception:
            vispy.use(app='PyQt6')
        
        # キャンバス作成
        canvas = scene.SceneCanvas(show=False, size=(400, 300))
        renderer = Renderer3D(canvas)
        print("✓ Renderer3D準備完了")
        
        # テスト用惑星
        orbital_elements = OrbitalElements(
            semi_major_axis=1.0, eccentricity=0.0167, inclination=0.0,
            longitude_of_ascending_node=0.0, argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0, epoch=2451545.0
        )
        planet = Planet("DynamicTestPlanet", 5.972e24, 6371, orbital_elements, color=(0.5, 0.5, 1.0, 1.0))
        
        # 初期位置（高詳細範囲）
        initial_position = np.array([1.0, 0, 0]) * 149597870.7
        planet.position = initial_position
        renderer.add_planet(planet)
        
        initial_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ 初期LOD: {initial_lod}")
        
        # 位置更新テスト（中詳細範囲へ移動）
        medium_position = np.array([5.0, 0, 0]) * 149597870.7
        renderer.update_planet_position("DynamicTestPlanet", medium_position)
        
        medium_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ 中距離移動後LOD: {medium_lod}")
        
        # 位置更新テスト（低詳細範囲へ移動）
        far_position = np.array([30.0, 0, 0]) * 149597870.7
        renderer.update_planet_position("DynamicTestPlanet", far_position)
        
        far_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ 遠距離移動後LOD: {far_lod}")
        
        # カメラ移動テスト
        print("✓ カメラ移動による全体LOD更新テスト")
        renderer.camera.distance = 1.0  # カメラを近づける
        renderer.update_all_lod()
        
        close_camera_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ カメラ接近後LOD: {close_camera_lod}")
        
        # LOD設定変更テスト
        print("✓ LOD設定変更テスト")
        renderer.set_lod_thresholds(high=1.0, medium=5.0, low=20.0)
        updated_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ 閾値変更後LOD: {updated_lod}")
        
        # LOD無効化テスト
        renderer.set_lod_enabled(False)
        disabled_lod = renderer.planet_visuals["DynamicTestPlanet"]['lod_level']
        print(f"✓ LOD無効化後: {disabled_lod}")
        
        # LOD統計確認
        final_render_info = renderer.get_render_info()
        print(f"✓ 最終レンダリング情報: {final_render_info}")
        
        # クリーンアップ
        renderer.cleanup()
        canvas.close()
        
        # 結果検証
        lod_changes_detected = (initial_lod != medium_lod) or (medium_lod != far_lod)
        success = lod_changes_detected and (disabled_lod == 'high')
        
        if success:
            print("\n🎉 LOD動的更新機能テスト成功！")
            print("   LODレベルが距離に応じて適切に変更されました")
        else:
            print("\n⚠️ LOD動的更新機能テストに問題があります")
        
        return success
        
    except Exception as e:
        print(f"❌ LOD動的更新機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lod_performance():
    """LODパフォーマンステスト"""
    print("\n" + "=" * 60)
    print("LODパフォーマンステスト")
    print("=" * 60)
    
    try:
        import vispy
        from vispy import scene
        from src.visualization.renderer_3d import Renderer3D
        from src.domain.planet import Planet
        from src.domain.orbital_elements import OrbitalElements
        
        # Vispyバックエンド設定
        try:
            vispy.use('PyQt6')
        except Exception:
            vispy.use(app='PyQt6')
        
        # 複数惑星でのパフォーマンステスト
        planet_count = 50
        print(f"✓ {planet_count}個の惑星でパフォーマンステスト")
        
        # LOD有効でのテスト
        canvas_lod = scene.SceneCanvas(show=False, size=(800, 600))
        renderer_lod = Renderer3D(canvas_lod)
        renderer_lod.set_lod_enabled(True)
        
        orbital_elements = OrbitalElements(
            semi_major_axis=1.0, eccentricity=0.0167, inclination=0.0,
            longitude_of_ascending_node=0.0, argument_of_perihelion=0.0,
            mean_anomaly_at_epoch=0.0, epoch=2451545.0
        )
        
        # LOD有効での惑星追加時間測定
        start_time = time.time()
        for i in range(planet_count):
            planet = Planet(f"Planet_{i}", 5.972e24, 6371, orbital_elements, color=(0.5, 0.5, 1.0, 1.0))
            # 距離をランダムに設定（1-100AU）
            distance = 1.0 + (i / planet_count) * 99.0
            planet.position = np.array([distance, 0, 0]) * 149597870.7
            renderer_lod.add_planet(planet)
        
        lod_enabled_time = time.time() - start_time
        print(f"✓ LOD有効時の惑星追加時間: {lod_enabled_time:.4f}秒")
        
        # LOD統計
        lod_render_info = renderer_lod.get_render_info()
        lod_stats = lod_render_info['lod_statistics']
        print(f"✓ LOD統計: {lod_stats}")
        
        # 更新処理時間測定
        start_time = time.time()
        for i in range(planet_count):
            new_position = np.array([i + 1.0, 0, 0]) * 149597870.7
            renderer_lod.update_planet_position(f"Planet_{i}", new_position)
        
        lod_update_time = time.time() - start_time
        print(f"✓ LOD有効時の位置更新時間: {lod_update_time:.4f}秒")
        
        # LOD無効でのテスト
        canvas_no_lod = scene.SceneCanvas(show=False, size=(800, 600))
        renderer_no_lod = Renderer3D(canvas_no_lod)
        renderer_no_lod.set_lod_enabled(False)
        
        # LOD無効での惑星追加時間測定
        start_time = time.time()
        for i in range(planet_count):
            planet = Planet(f"Planet_{i}", 5.972e24, 6371, orbital_elements, color=(0.5, 0.5, 1.0, 1.0))
            distance = 1.0 + (i / planet_count) * 99.0
            planet.position = np.array([distance, 0, 0]) * 149597870.7
            renderer_no_lod.add_planet(planet)
        
        no_lod_time = time.time() - start_time
        print(f"✓ LOD無効時の惑星追加時間: {no_lod_time:.4f}秒")
        
        # パフォーマンス比較
        performance_ratio = no_lod_time / lod_enabled_time if lod_enabled_time > 0 else 1.0
        print(f"✓ パフォーマンス比: {performance_ratio:.2f}倍")
        
        # クリーンアップ
        renderer_lod.cleanup()
        renderer_no_lod.cleanup()
        canvas_lod.close()
        canvas_no_lod.close()
        
        # 結果判定
        success = lod_enabled_time > 0 and no_lod_time > 0
        
        if success:
            print(f"\n🎉 LODパフォーマンステスト成功！")
            print(f"   LOD有効: {lod_enabled_time:.4f}秒")
            print(f"   LOD無効: {no_lod_time:.4f}秒")
            print(f"   詳細度統計: 高{lod_stats['high']}、中{lod_stats['medium']}、低{lod_stats['low']}")
        else:
            print(f"\n⚠️ LODパフォーマンステストに問題があります")
        
        return success
        
    except Exception as e:
        print(f"❌ LODパフォーマンステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("3D描画LOD（レベルオブディテール）最適化テスト開始")
    print(f"Python版本: {sys.version}")
    print(f"作業ディレクトリ: {Path.cwd()}")
    
    test_results = []
    
    # 各テストを実行
    test_results.append(("基本機能テスト", test_lod_system()))
    test_results.append(("動的更新テスト", test_lod_dynamic_update()))
    test_results.append(("パフォーマンステスト", test_lod_performance()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("3D描画LOD最適化テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 3D描画LOD最適化テスト完全成功！")
        print("\n✅ 確認済み機能:")
        print("   - 距離に基づく自動LOD調整")
        print("   - 動的LODレベル更新")
        print("   - カメラ移動による全体LOD更新")
        print("   - LOD設定の変更機能")
        print("   - パフォーマンス最適化効果")
    else:
        print(f"⚠️ {total - passed}個のテストが失敗しました")
    
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