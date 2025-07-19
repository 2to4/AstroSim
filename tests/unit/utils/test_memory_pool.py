"""
メモリプール管理システムのテスト

ObjectPoolとMemoryPoolManagerの動作を検証します。
"""

import pytest
import numpy as np
import gc
import weakref
from unittest.mock import Mock, patch

from src.utils.memory_pool import (
    ObjectPool, MemoryPoolManager, 
    get_memory_pool, reset_memory_pool
)


class TestObjectPool:
    """ObjectPoolクラスのテスト"""
    
    def test_pool_initialization(self):
        """プールの初期化テスト"""
        # 基本的な初期化
        pool = ObjectPool(list)
        assert pool.object_class == list
        assert pool.max_pool_size == 100
        assert len(pool._available) == 0
        assert len(pool._in_use) == 0
        
        # カスタム初期化
        factory = lambda x=10: [0] * x
        reset = lambda obj, x=10: obj.clear()
        pool = ObjectPool(list, factory_func=factory, reset_func=reset, max_pool_size=50)
        assert pool.max_pool_size == 50
        assert pool.factory_func == factory
        assert pool.reset_func == reset
    
    def test_acquire_new_object(self):
        """新規オブジェクト取得のテスト"""
        pool = ObjectPool(list)
        
        # 新規取得
        obj1 = pool.acquire()
        assert isinstance(obj1, list)
        # listは弱参照できないので、_in_use_fallbackに入る
        assert id(obj1) in pool._in_use_fallback
        assert pool._stats['created'] == 1
        assert pool._stats['reused'] == 0
        
        # 複数取得
        obj2 = pool.acquire()
        obj3 = pool.acquire()
        assert obj1 is not obj2
        assert obj2 is not obj3
        assert len(pool._in_use_fallback) == 3
        assert pool._stats['created'] == 3
    
    def test_release_and_reuse(self):
        """オブジェクトの返却と再利用のテスト"""
        pool = ObjectPool(list)
        
        # オブジェクトを取得して返却
        obj1 = pool.acquire()
        obj1.append("test")
        pool.release(obj1)
        
        assert id(obj1) not in pool._in_use_fallback
        assert len(pool._available) == 1
        assert pool._stats['released'] == 1
        
        # 再利用
        obj2 = pool.acquire()
        assert obj2 is obj1  # 同じオブジェクトが返される
        assert pool._stats['reused'] == 1
        assert pool._stats['created'] == 1  # 新規作成は増えない
    
    def test_reset_function(self):
        """リセット関数のテスト"""
        reset_called = False
        reset_kwargs = {}
        
        def reset_func(obj, **kwargs):
            nonlocal reset_called, reset_kwargs
            reset_called = True
            reset_kwargs = kwargs
            obj.clear()
            obj.extend([kwargs.get('value', 0)])
        
        pool = ObjectPool(list, reset_func=reset_func)
        
        # オブジェクトを取得・返却・再取得
        obj1 = pool.acquire()
        obj1.extend([1, 2, 3])
        pool.release(obj1)
        
        obj2 = pool.acquire(value=42)
        assert reset_called
        assert reset_kwargs == {'value': 42}
        assert obj2 == [42]
    
    def test_max_pool_size(self):
        """プールサイズ制限のテスト"""
        pool = ObjectPool(list, max_pool_size=2)
        
        # 3つのオブジェクトを作成
        objs = [pool.acquire() for _ in range(3)]
        
        # 全て返却
        for obj in objs:
            pool.release(obj)
        
        # プールには2つまでしか保持されない
        assert len(pool._available) == 2
        assert pool._stats['destroyed'] == 1
    
    def test_clear_pool(self):
        """プールクリアのテスト"""
        pool = ObjectPool(list)
        
        # オブジェクトを作成して返却
        objs = [pool.acquire() for _ in range(5)]
        for obj in objs[:3]:
            pool.release(obj)
        
        assert len(pool._available) == 3
        assert len(pool._in_use_fallback) == 2
        
        # プールをクリア
        pool.clear()
        assert len(pool._available) == 0
        assert len(pool._in_use_fallback) == 2  # 使用中はそのまま
    
    def test_weak_reference_cleanup(self):
        """弱参照によるクリーンアップのテスト"""
        # 弱参照可能なオブジェクトを使用するカスタムクラス
        class WeakRefable:
            pass
        
        pool = ObjectPool(WeakRefable)
        
        # オブジェクトを取得
        obj = pool.acquire()
        assert len(pool._in_use) == 1
        
        # オブジェクトを削除（ガベージコレクション）
        del obj
        gc.collect()
        
        # 弱参照なので自動的にクリーンアップされる
        assert len(pool._in_use) == 0


class TestMemoryPoolManager:
    """MemoryPoolManagerクラスのテスト"""
    
    def test_manager_initialization(self):
        """マネージャーの初期化テスト"""
        manager = MemoryPoolManager(memory_limit_mb=256.0)
        assert manager.memory_limit_mb == 256.0
        assert len(manager._pools) > 0  # デフォルトプールが初期化される
        
        # Vispyプールの確認
        assert 'sphere_high' in manager._pools
        assert 'sphere_medium' in manager._pools
        assert 'sphere_low' in manager._pools
        assert 'text_label' in manager._pools
        assert 'orbit_line' in manager._pools
    
    def test_register_custom_pool(self):
        """カスタムプールの登録テスト"""
        manager = MemoryPoolManager()
        
        # カスタムクラス
        class CustomObject:
            def __init__(self, value=0):
                self.value = value
        
        # プール登録
        manager.register_pool(
            'custom',
            CustomObject,
            factory_func=lambda: CustomObject(42),
            max_pool_size=10
        )
        
        assert 'custom' in manager._pools
        obj = manager.acquire('custom')
        assert isinstance(obj, CustomObject)
        assert obj.value == 42
    
    def test_acquire_and_release(self):
        """オブジェクトの取得と返却のテスト"""
        manager = MemoryPoolManager()
        
        # 存在しないプールからの取得
        with pytest.raises(KeyError):
            manager.acquire('nonexistent')
        
        # テキストラベルの取得
        label1 = manager.acquire('text_label', text='Hello', color=(1, 0, 0, 1))
        assert label1 is not None
        
        # 返却と再取得
        manager.release('text_label', label1)
        label2 = manager.acquire('text_label', text='World')
        assert label2 is label1  # 再利用される
    
    def test_memory_stats(self):
        """メモリ統計情報のテスト"""
        manager = MemoryPoolManager()
        
        # オブジェクトを取得
        objs = []
        for i in range(5):
            objs.append(manager.acquire('text_label'))
        
        stats = manager.get_memory_stats()
        assert 'memory_usage_mb' in stats
        assert 'memory_limit_mb' in stats
        assert 'usage_ratio' in stats
        assert 'total_objects' in stats
        assert 'pools' in stats
        
        # プール統計の確認
        text_stats = stats['pools']['text_label']
        assert text_stats['created'] == 5
        assert text_stats['in_use'] == 5
    
    @patch('psutil.Process')
    def test_memory_check_and_gc(self, mock_process):
        """メモリチェックとGC実行のテスト"""
        # メモリ使用量をモック
        mock_memory_info = Mock()
        mock_memory_info.rss = 450 * 1024 * 1024  # 450MB
        mock_process.return_value.memory_info.return_value = mock_memory_info
        
        manager = MemoryPoolManager(memory_limit_mb=500.0)
        
        # 多数のオブジェクトを作成して返却
        for _ in range(20):
            obj = manager.acquire('text_label')
            manager.release('text_label', obj)
        
        # メモリ使用率が高い状態で取得（GCトリガー）
        with patch.object(manager, '_run_garbage_collection') as mock_gc:
            manager.acquire('text_label')
            mock_gc.assert_called_once()
    
    def test_optimize_memory(self):
        """メモリ最適化のテスト"""
        manager = MemoryPoolManager()
        
        # オブジェクトを作成して全て返却
        objs = []
        for _ in range(10):
            obj = manager.acquire('text_label')
            objs.append(obj)
        
        for obj in objs:
            manager.release('text_label', obj)
        
        # 最適化前の統計
        before_stats = manager.get_memory_stats()
        text_pool_before = before_stats['pools']['text_label']
        assert text_pool_before['available'] == 10
        
        # メモリ最適化実行
        manager.optimize_memory()
        
        # 最適化後の統計
        after_stats = manager.get_memory_stats()
        text_pool_after = after_stats['pools']['text_label']
        # 利用可能数が削減されているはず
        assert text_pool_after['available'] < text_pool_before['available']
    
    def test_numpy_array_pools(self):
        """NumPy配列プールのテスト"""
        manager = MemoryPoolManager()
        
        # 360x3配列の取得
        arr1 = manager.acquire('numpy_array_360x3')
        assert isinstance(arr1, np.ndarray)
        assert arr1.shape == (360, 3)
        assert np.all(arr1 == 0)
        
        # 配列に値を設定
        arr1.fill(1.5)
        
        # 返却と再取得
        manager.release('numpy_array_360x3', arr1)
        arr2 = manager.acquire('numpy_array_360x3')
        
        # リセットされているはず
        assert arr2 is arr1
        assert np.all(arr2 == 0)
    
    def test_clear_all(self):
        """全プールクリアのテスト"""
        manager = MemoryPoolManager()
        
        # 各プールからオブジェクトを取得
        objs = []
        for pool_name in ['text_label', 'sphere_high', 'orbit_line']:
            for _ in range(3):
                obj = manager.acquire(pool_name)
                objs.append((pool_name, obj))
        
        # いくつか返却
        for pool_name, obj in objs[:5]:
            manager.release(pool_name, obj)
        
        # 全プールクリア
        manager.clear_all()
        
        # 各プールが空になっているか確認
        stats = manager.get_memory_stats()
        for pool_stats in stats['pools'].values():
            assert pool_stats['available'] == 0


class TestGlobalMemoryPool:
    """グローバルメモリプール関数のテスト"""
    
    def test_get_memory_pool_singleton(self):
        """シングルトンパターンのテスト"""
        reset_memory_pool()  # 初期化
        
        pool1 = get_memory_pool()
        pool2 = get_memory_pool()
        
        assert pool1 is pool2  # 同じインスタンス
        assert isinstance(pool1, MemoryPoolManager)
    
    def test_reset_memory_pool(self):
        """メモリプールリセットのテスト"""
        # プールを取得して使用
        pool1 = get_memory_pool()
        obj = pool1.acquire('text_label')
        
        # リセット
        reset_memory_pool()
        
        # 新しいプール
        pool2 = get_memory_pool()
        assert pool1 is not pool2  # 異なるインスタンス


@pytest.mark.performance
class TestMemoryPoolPerformance:
    """メモリプールのパフォーマンステスト"""
    
    def test_allocation_performance(self):
        """オブジェクト割り当てのパフォーマンス比較"""
        import time
        manager = MemoryPoolManager()
        
        def measure_time(func, iterations=3):
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                func()
                end = time.perf_counter()
                times.append(end - start)
            return min(times)  # 最小時間を使用
        
        def with_pool():
            # プールを使用
            objs = []
            for _ in range(100):
                obj = manager.acquire('text_label')
                objs.append(obj)
            for obj in objs:
                manager.release('text_label', obj)
        
        def without_pool():
            # 直接作成
            objs = []
            for _ in range(100):
                obj = {'text': '', 'color': (1, 1, 1, 1)}
                objs.append(obj)
            objs.clear()
        
        # ウォームアップ
        with_pool()
        
        # パフォーマンス測定
        pool_time = measure_time(with_pool)
        direct_time = measure_time(without_pool)
        
        # プールを使用した方が高速または同等であることを確認
        # （初回のオブジェクト作成コストを除けば、プールは高速）
        print(f"\nPool time: {pool_time:.6f}s, Direct time: {direct_time:.6f}s")
        assert pool_time < direct_time * 2.0  # 最悪でも2倍以内