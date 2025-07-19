#!/usr/bin/env python3
"""
フラスタムカリングのデバッグ用スクリプト
"""

import numpy as np
from src.utils.frustum_culling import Frustum, BoundingSphere

def debug_frustum():
    """フラスタムの動作をデバッグ"""
    print("=== フラスタムカリング デバッグ ===")
    
    # カメラパラメータ
    camera_params = {
        'position': np.array([0, 0, 10]),
        'center': np.array([0, 0, 0]),
        'fov': 60.0,
        'aspect_ratio': 1.0,
        'near': 0.1,
        'far': 100.0,
        'up': np.array([0, 1, 0])
    }
    
    print(f"カメラ位置: {camera_params['position']}")
    print(f"注視点: {camera_params['center']}")
    print(f"視野角: {camera_params['fov']}度")
    
    # フラスタムを作成
    frustum = Frustum()
    frustum.update_from_camera(camera_params)
    
    print(f"\n作成された平面数: {len(frustum.planes)}")
    
    # 各平面を表示
    for i, plane in enumerate(frustum.planes):
        print(f"平面{i}: 法線={plane.normal}, 距離={plane.distance}")
    
    # テスト点
    test_points = [
        ("原点", np.array([0, 0, 0])),
        ("カメラ前方1", np.array([0, 0, 1])),
        ("カメラ前方5", np.array([0, 0, 5])),
        ("カメラ後方", np.array([0, 0, 15])),
        ("遠方", np.array([0, 0, -200])),
        ("横", np.array([10, 0, 5])),
        # 惑星位置のテスト
        ("Mercury", np.array([0.38, 0, 0])),
        ("Venus", np.array([0.72, 0, 0])),
        ("Earth", np.array([1.0, 0, 0])),
        ("Mars", np.array([1.52, 0, 0])),
    ]
    
    print("\n=== 点の可視判定 ===")
    for name, point in test_points:
        visible = frustum.is_point_visible(point)
        print(f"{name} {point}: {'可視' if visible else '不可視'}")
        
        # 各平面との関係を詳細表示
        for i, plane in enumerate(frustum.planes):
            distance = plane.distance_to_point(point)
            print(f"  平面{i}: 距離={distance:.3f}")
    
    # テスト球
    test_spheres = [
        ("球1", BoundingSphere(np.array([0, 0, 1]), 1.0)),
        ("球2", BoundingSphere(np.array([0, 0, 5]), 1.0)),
        ("球3", BoundingSphere(np.array([0, 0, 15]), 1.0)),
    ]
    
    print("\n=== 球の可視判定 ===")
    for name, sphere in test_spheres:
        visible = frustum.is_sphere_visible(sphere)
        print(f"{name} 中心={sphere.center}, 半径={sphere.radius}: {'可視' if visible else '不可視'}")

if __name__ == "__main__":
    debug_frustum()