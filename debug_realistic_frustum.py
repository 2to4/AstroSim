#!/usr/bin/env python3
"""
実際的なシナリオでのフラスタムカリングのデバッグ用スクリプト
"""

import numpy as np
from src.utils.frustum_culling import FrustumCuller, BoundingSphere

def debug_realistic_scenario():
    """実際的なシナリオでのフラスタムカリングをデバッグ"""
    print("=== 実際的なシナリオ フラスタムカリング デバッグ ===")
    
    culler = FrustumCuller()
    
    # 太陽系の惑星を模擬
    planets = {
        "Mercury": (0.38, 0.5),   # (軌道半径AU, 惑星半径相対値)
        "Venus": (0.72, 0.9),
        "Earth": (1.0, 1.0),
        "Mars": (1.52, 0.5),
        "Jupiter": (5.2, 11.0),
        "Saturn": (9.5, 9.0),
        "Uranus": (19.2, 4.0),
        "Neptune": (30.0, 3.9),
    }
    
    # 惑星を登録
    for name, (orbit_radius, planet_radius) in planets.items():
        culler.register_object(name, np.array([0, 0, 0]), planet_radius * 0.01)
        print(f"{name}: 軌道半径={orbit_radius}AU, 惑星半径={planet_radius * 0.01}")
    
    # 地球付近からの視点
    camera_params = {
        'position': np.array([1.5, 0, 0.5]),
        'center': np.array([0, 0, 0]),
        'fov': 60.0,
        'aspect_ratio': 16/9,
        'near': 0.001,
        'far': 20.0  # 20AU（天王星まで）
    }
    
    print(f"\nカメラ位置: {camera_params['position']}")
    print(f"注視点: {camera_params['center']}")
    print(f"視野角: {camera_params['fov']}度")
    print(f"遠クリップ面: {camera_params['far']}AU")
    
    culler.update_frustum(camera_params)
    
    # フラスタム情報を表示
    frustum = culler.frustum
    print(f"\n作成された平面数: {len(frustum.planes)}")
    for i, plane in enumerate(frustum.planes):
        print(f"平面{i}: 法線={plane.normal}, 距離={plane.distance}")
    
    # 惑星位置（簡略化：X軸上に配置）
    positions = {}
    for name, (orbit_radius, _) in planets.items():
        positions[name] = np.array([orbit_radius, 0, 0])
    
    print("\n=== 各惑星の可視性判定 ===")
    for name in planets.keys():
        pos = positions[name]
        orbit_radius, planet_radius = planets[name]
        
        # 点での判定
        point_visible = frustum.is_point_visible(pos)
        
        # 球での判定
        sphere = BoundingSphere(pos, planet_radius * 0.01)
        sphere_visible = frustum.is_sphere_visible(sphere)
        
        print(f"{name} (位置: {pos})")
        print(f"  点での判定: {'可視' if point_visible else '不可視'}")
        print(f"  球での判定: {'可視' if sphere_visible else '不可視'}")
        
        # 各平面との距離を表示
        for i, plane in enumerate(frustum.planes):
            distance = plane.distance_to_point(pos)
            print(f"  平面{i}: 距離={distance:.3f}")
        print()
    
    # カリング実行
    visible = culler.cull_objects(positions)
    
    print("=== カリング結果 ===")
    print(f"可視惑星: {visible}")
    print(f"不可視惑星: {[name for name in planets.keys() if name not in visible]}")
    
    # 統計情報
    stats = culler.get_stats()
    print(f"\n=== 統計情報 ===")
    print(f"フレーム数: {stats['frame_count']}")
    print(f"チェック済み: {stats['total_checked']}")
    print(f"カリング済み: {stats['total_culled']}")
    print(f"平均カリング率: {stats['average_cull_ratio']:.1%}")

if __name__ == "__main__":
    debug_realistic_scenario()