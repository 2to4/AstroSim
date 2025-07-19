#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
軌道計算キャッシュ機構テストスクリプト

OrbitCalculatorの新しいキャッシュ機能のパフォーマンスと
正確性をテストします。
"""

import sys
import time
import numpy as np
from pathlib import Path

# Windows環境でのエンコーディング設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import tempfile

from src.simulation.orbit_calculator import OrbitCalculator
from src.domain.orbital_elements import OrbitalElements
from src.data.data_loader import DataLoader

def test_orbit_cache_performance():
    """軌道計算キャッシュのパフォーマンステスト"""
    print("=" * 60)
    print("軌道計算キャッシュパフォーマンステスト")
    print("=" * 60)
    
    # OrbitCalculator初期化
    calculator = OrbitCalculator()
    
    # 地球の軌道要素（固定データ）
    orbital_elements = OrbitalElements(
        semi_major_axis=1.00000261,  # AU (地球)
        eccentricity=0.01671123,
        inclination=0.00005,  # 度
        longitude_of_ascending_node=348.73936,
        argument_of_perihelion=114.20783,
        mean_anomaly_at_epoch=357.51716,
        epoch=2451545.0  # J2000.0
    )
    print(f"✓ 地球軌道要素設定完了")
    
    # テスト設定
    test_iterations = 1000
    time_range_days = 365.25  # 1年間
    julian_dates = [2451545.0 + (i * time_range_days / test_iterations) for i in range(test_iterations)]
    
    print(f"✓ テスト設定: {test_iterations}回計算、{time_range_days:.1f}日間")
    
    # キャッシュなしでの計算時間測定
    calculator.clear_cache()
    start_time = time.time()
    
    results_no_cache = []
    for julian_date in julian_dates:
        position, velocity = calculator.calculate_position_velocity(orbital_elements, julian_date)
        results_no_cache.append((position.copy(), velocity.copy()))
    
    time_no_cache = time.time() - start_time
    print(f"✓ キャッシュなし計算時間: {time_no_cache:.4f}秒")
    
    # キャッシュ統計（最初の実行後）
    cache_stats = calculator.get_cache_stats()
    print(f"✓ キャッシュ統計: {cache_stats}")
    
    # 同じ計算を再実行（キャッシュ効果確認）
    start_time = time.time()
    
    results_with_cache = []
    for julian_date in julian_dates:
        position, velocity = calculator.calculate_position_velocity(orbital_elements, julian_date)
        results_with_cache.append((position.copy(), velocity.copy()))
    
    time_with_cache = time.time() - start_time
    print(f"✓ キャッシュあり計算時間: {time_with_cache:.4f}秒")
    
    # 最終キャッシュ統計
    final_cache_stats = calculator.get_cache_stats()
    print(f"✓ 最終キャッシュ統計: {final_cache_stats}")
    
    # パフォーマンス向上計算
    speedup = time_no_cache / time_with_cache if time_with_cache > 0 else float('inf')
    print(f"✓ パフォーマンス向上: {speedup:.2f}倍")
    
    # 結果の一致性確認
    all_positions_match = True
    all_velocities_match = True
    
    for i, ((pos1, vel1), (pos2, vel2)) in enumerate(zip(results_no_cache, results_with_cache)):
        if not np.allclose(pos1, pos2, atol=1e-10):
            print(f"❌ 位置不一致 at index {i}: {pos1} vs {pos2}")
            all_positions_match = False
            break
        if not np.allclose(vel1, vel2, atol=1e-10):
            print(f"❌ 速度不一致 at index {i}: {vel1} vs {vel2}")
            all_velocities_match = False
            break
    
    if all_positions_match:
        print("✓ 全ての位置計算結果が一致")
    if all_velocities_match:
        print("✓ 全ての速度計算結果が一致")
    
    success = all_positions_match and all_velocities_match and speedup > 1.5
    
    if success:
        print("\n🎉 軌道計算キャッシュテスト成功！")
        print(f"   {speedup:.1f}倍のパフォーマンス向上を確認")
        print(f"   キャッシュヒット率: {final_cache_stats['cache_hit_rate_percent']:.1f}%")
    else:
        print("\n⚠️ 軌道計算キャッシュテストに問題があります")
    
    return success

def test_cache_accuracy():
    """キャッシュの精度テスト"""
    print("\n" + "=" * 60)
    print("軌道計算キャッシュ精度テスト")
    print("=" * 60)
    
    calculator = OrbitCalculator()
    
    # テスト用軌道要素
    orbital_elements = OrbitalElements(
        semi_major_axis=1.0,  # 1 AU
        eccentricity=0.0167,  # 地球に近い離心率
        inclination=7.155,    # 黄道に対する傾斜
        longitude_of_ascending_node=348.74,
        argument_of_perihelion=114.21,
        mean_anomaly_at_epoch=357.52,
        epoch=2451545.0  # J2000.0
    )
    
    # 異なる時刻での計算
    test_times = [2451545.0 + i * 0.1 for i in range(20)]  # 0.1日刻み
    
    # 最初の計算（キャッシュに保存）
    initial_results = []
    for julian_date in test_times:
        result = calculator.calculate_position_velocity(orbital_elements, julian_date)
        initial_results.append(result)
    
    print(f"✓ 初期計算完了: {len(initial_results)}件")
    
    # キャッシュ統計確認
    cache_stats = calculator.get_cache_stats()
    print(f"✓ キャッシュサイズ: {cache_stats['cache_size']}")
    
    # 同じ時刻での再計算（キャッシュから取得）
    cached_results = []
    for julian_date in test_times:
        result = calculator.calculate_position_velocity(orbital_elements, julian_date)
        cached_results.append(result)
    
    # 再計算後のキャッシュ統計
    after_cache_stats = calculator.get_cache_stats()
    print(f"✓ 再計算後キャッシュ統計: {after_cache_stats}")
    
    # 精度比較
    max_position_error = 0.0
    max_velocity_error = 0.0
    
    for i, ((pos1, vel1), (pos2, vel2)) in enumerate(zip(initial_results, cached_results)):
        pos_error = np.linalg.norm(pos1 - pos2)
        vel_error = np.linalg.norm(vel1 - vel2)
        
        max_position_error = max(max_position_error, pos_error)
        max_velocity_error = max(max_velocity_error, vel_error)
    
    print(f"✓ 最大位置誤差: {max_position_error:.2e} km")
    print(f"✓ 最大速度誤差: {max_velocity_error:.2e} km/s")
    
    # 許容誤差内かチェック
    position_accuracy = max_position_error < 1e-10  # 1e-10 km = 0.1 mm
    velocity_accuracy = max_velocity_error < 1e-13  # 1e-13 km/s = 0.1 mm/s
    
    final_cache_stats = calculator.get_cache_stats()
    hit_rate = final_cache_stats['cache_hit_rate_percent']
    
    # 精度テストでは同じ時刻の再計算なので100%ヒット率が期待される
    success = position_accuracy and velocity_accuracy and hit_rate > 90
    
    if success:
        print(f"\n🎉 キャッシュ精度テスト成功！")
        print(f"   ヒット率: {hit_rate:.1f}%")
        print(f"   位置精度: {max_position_error:.2e} km")
        print(f"   速度精度: {max_velocity_error:.2e} km/s")
    else:
        print(f"\n⚠️ キャッシュ精度テストに問題があります")
    
    return success

def test_cache_memory_management():
    """キャッシュメモリ管理テスト"""
    print("\n" + "=" * 60)
    print("キャッシュメモリ管理テスト")
    print("=" * 60)
    
    calculator = OrbitCalculator()
    
    # 小さなキャッシュサイズに設定
    calculator.cache_max_size = 100
    
    # 大量の異なる時刻での計算（キャッシュサイズを超える）
    test_count = 150
    orbital_elements = OrbitalElements(
        semi_major_axis=1.0,
        eccentricity=0.0167,
        inclination=0.0,
        longitude_of_ascending_node=0.0,
        argument_of_perihelion=0.0,
        mean_anomaly_at_epoch=0.0,
        epoch=2451545.0
    )
    
    for i in range(test_count):
        julian_date = 2451545.0 + i * 1.0  # 1日刻み
        calculator.calculate_position_velocity(orbital_elements, julian_date)
    
    cache_stats = calculator.get_cache_stats()
    cache_size = cache_stats['cache_size']
    
    print(f"✓ 計算実行: {test_count}回")
    print(f"✓ 最大キャッシュサイズ: {calculator.cache_max_size}")
    print(f"✓ 実際のキャッシュサイズ: {cache_size}")
    print(f"✓ キャッシュ統計: {cache_stats}")
    
    # キャッシュサイズが制限内かチェック
    size_within_limit = cache_size <= calculator.cache_max_size
    
    if size_within_limit:
        print(f"\n🎉 メモリ管理テスト成功！")
        print(f"   キャッシュサイズが制限内: {cache_size}/{calculator.cache_max_size}")
    else:
        print(f"\n❌ メモリ管理テスト失敗")
        print(f"   キャッシュサイズが制限超過: {cache_size}/{calculator.cache_max_size}")
    
    return size_within_limit

def main():
    """メインテスト実行"""
    print("軌道計算キャッシュ機構 総合テスト開始")
    print(f"Python版本: {sys.version}")
    print(f"作業ディレクトリ: {Path.cwd()}")
    
    test_results = []
    
    # 各テストを実行
    test_results.append(("パフォーマンステスト", test_orbit_cache_performance()))
    test_results.append(("精度テスト", test_cache_accuracy()))
    test_results.append(("メモリ管理テスト", test_cache_memory_management()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("軌道計算キャッシュテスト結果サマリー")
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
        print("🎉 軌道計算キャッシュ機構テスト完全成功！")
        print("\n✅ 確認済み機能:")
        print("   - 軌道計算結果の正確なキャッシュ")
        print("   - 大幅なパフォーマンス向上")
        print("   - メモリ使用量の適切な制限")
        print("   - キャッシュヒット率の最適化")
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