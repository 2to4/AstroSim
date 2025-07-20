"""
メモリプール管理システムの実装

オブジェクトの再利用によるメモリアロケーションの最適化、
ガベージコレクションの負荷軽減を実現します。
"""

import weakref
from typing import Dict, List, Optional, Type, Any, Callable
from collections import defaultdict
import gc
import psutil
import logging
from datetime import datetime
import numpy as np
from vispy import scene


logger = logging.getLogger(__name__)


class ObjectPool:
    """
    汎用オブジェクトプール
    
    オブジェクトの作成・破棄のオーバーヘッドを削減し、
    メモリの効率的な再利用を実現します。
    """
    
    def __init__(self, 
                 object_class: Type,
                 factory_func: Optional[Callable] = None,
                 reset_func: Optional[Callable] = None,
                 max_pool_size: int = 100):
        """
        オブジェクトプールの初期化
        
        Args:
            object_class: プールするオブジェクトのクラス
            factory_func: オブジェクト生成関数（Noneの場合はデフォルトコンストラクタ）
            reset_func: オブジェクトリセット関数
            max_pool_size: プールの最大サイズ
        """
        self.object_class = object_class
        self.factory_func = factory_func or (lambda: object_class())
        self.reset_func = reset_func
        self.max_pool_size = max_pool_size
        
        # 利用可能なオブジェクトプール
        self._available: List[Any] = []
        
        # 使用中のオブジェクト（弱参照で管理）
        # 注意: 一部のオブジェクト（list、dict等）は弱参照を作成できない
        self._in_use: weakref.WeakSet = weakref.WeakSet()
        self._in_use_fallback: set = set()  # 弱参照できないオブジェクト用
        
        # 統計情報
        self._stats = {
            'created': 0,
            'reused': 0,
            'released': 0,
            'destroyed': 0
        }
    
    def acquire(self, **kwargs) -> Any:
        """
        プールからオブジェクトを取得
        
        Args:
            **kwargs: オブジェクト初期化用のパラメータ
            
        Returns:
            取得したオブジェクト
        """
        if self._available:
            # プールから再利用
            obj = self._available.pop()
            self._stats['reused'] += 1
            
            # リセット処理
            if self.reset_func:
                self.reset_func(obj, **kwargs)
        else:
            # 新規作成
            obj = self.factory_func(**kwargs)
            self._stats['created'] += 1
        
        # 使用中リストに追加
        try:
            self._in_use.add(obj)
        except TypeError:
            # 弱参照を作成できないオブジェクトの場合
            self._in_use_fallback.add(id(obj))
        
        return obj
    
    def release(self, obj: Any) -> None:
        """
        オブジェクトをプールに返却
        
        Args:
            obj: 返却するオブジェクト
        """
        # 使用中チェック
        try:
            in_weak_set = obj in self._in_use
        except (TypeError, ValueError):
            # 弱参照チェックができない場合
            in_weak_set = False
        in_fallback = id(obj) in self._in_use_fallback
        
        if not in_weak_set and not in_fallback:
            return
        
        # 使用中リストから削除
        if in_weak_set:
            self._in_use.discard(obj)
        if in_fallback:
            self._in_use_fallback.discard(id(obj))
        
        self._stats['released'] += 1
        
        # プールサイズチェック
        if len(self._available) < self.max_pool_size:
            self._available.append(obj)
        else:
            # プールが満杯の場合は破棄
            self._destroy_object(obj)
            self._stats['destroyed'] += 1
    
    def _destroy_object(self, obj: Any) -> None:
        """オブジェクトの破棄処理"""
        # Vispyオブジェクトの場合は親から切り離す
        if hasattr(obj, 'parent') and obj.parent is not None:
            obj.parent = None
        
        # NumPy配列の場合は明示的に削除
        if isinstance(obj, np.ndarray):
            del obj
    
    def clear(self) -> None:
        """プールを空にする"""
        # 使用中のオブジェクトはそのまま
        # 利用可能なオブジェクトを全て破棄
        for obj in self._available:
            self._destroy_object(obj)
        
        self._available.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """統計情報を取得"""
        return {
            **self._stats,
            'available': len(self._available),
            'in_use': len(self._in_use) + len(self._in_use_fallback)
        }


class MemoryPoolManager:
    """
    メモリプール管理マネージャー
    
    アプリケーション全体のメモリプールを統合管理し、
    メモリ使用量の監視と最適化を行います。
    """
    
    def __init__(self, memory_limit_mb: float = 500.0):
        """
        メモリプールマネージャーの初期化
        
        Args:
            memory_limit_mb: メモリ使用量の上限（MB）
        """
        self.memory_limit_mb = memory_limit_mb
        self._pools: Dict[str, ObjectPool] = {}
        self._memory_usage_history: List[Dict[str, Any]] = []
        self._gc_threshold = 0.8  # メモリ使用率80%でGCトリガー
        self.auto_gc_enabled = True  # 自動GC機能の有効無効
        
        # Vispy専用プールの初期化
        self._initialize_vispy_pools()
        
        # NumPy配列プールの初期化
        self._initialize_numpy_pools()
    
    def _initialize_vispy_pools(self) -> None:
        """Vispyオブジェクト用のプールを初期化"""
        # 球体プール（LOD別）
        for lod in ['high', 'medium', 'low']:
            subdivisions = {'high': 32, 'medium': 16, 'low': 8}[lod]
            
            def sphere_factory(radius=1.0, color=(1, 1, 1, 1), parent=None, 
                             subdivisions=subdivisions):
                return scene.visuals.Sphere(
                    radius=radius,
                    color=color,
                    subdivisions=subdivisions,
                    parent=parent
                )
            
            def sphere_reset(sphere, radius=1.0, color=(1, 1, 1, 1), parent=None, **kwargs):
                sphere.radius = radius
                sphere.color = color
                sphere.parent = parent
                # transformはNoneに設定できないので、初期値に戻す
                if hasattr(sphere, 'transform'):
                    from vispy.visuals.transforms import STTransform
                    sphere.transform = STTransform()
            
            self.register_pool(
                f'sphere_{lod}',
                scene.visuals.Sphere,
                factory_func=sphere_factory,
                reset_func=sphere_reset,
                max_pool_size=50
            )
        
        # テキストラベルプール
        def text_factory(text='', color=(1, 1, 1, 1), font_size=12, parent=None):
            return scene.visuals.Text(
                text=text,
                color=color,
                font_size=font_size,
                parent=parent
            )
        
        def text_reset(text_obj, text='', color=(1, 1, 1, 1), parent=None, **kwargs):
            text_obj.text = text
            text_obj.color = color
            text_obj.parent = parent
            # transformはNoneに設定できないので、初期値に戻す
            if hasattr(text_obj, 'transform'):
                try:
                    from vispy.visuals.transforms import STTransform
                    text_obj.transform = STTransform()
                except (ImportError, AttributeError):
                    # テスト環境やvispyが不完全な場合はスキップ
                    pass
        
        self.register_pool(
            'text_label',
            scene.visuals.Text,
            factory_func=text_factory,
            reset_func=text_reset,
            max_pool_size=100
        )
        
        # 軌道線プール
        def line_factory(pos=None, color=(0.5, 0.5, 0.5, 0.3), width=1.0, parent=None):
            if pos is None:
                pos = np.zeros((2, 3))
            return scene.visuals.Line(
                pos=pos,
                color=color,
                width=width,
                parent=parent
            )
        
        def line_reset(line, pos=None, color=(0.5, 0.5, 0.5, 0.3), parent=None, **kwargs):
            if pos is not None:
                line.set_data(pos=pos, color=color)
            line.parent = parent
            # transformはNoneに設定できないので、初期値に戻す
            if hasattr(line, 'transform'):
                from vispy.visuals.transforms import STTransform
                line.transform = STTransform()
        
        self.register_pool(
            'orbit_line',
            scene.visuals.Line,
            factory_func=line_factory,
            reset_func=line_reset,
            max_pool_size=50
        )
    
    def _initialize_numpy_pools(self) -> None:
        """NumPy配列用のプールを初期化"""
        # 軌道計算用の配列プール
        sizes = [(360, 3), (100, 3), (1000, 3)]  # 一般的なサイズ
        
        for size in sizes:
            pool_name = f'numpy_array_{size[0]}x{size[1]}'
            
            def array_factory(size=size):
                return np.zeros(size, dtype=np.float64)
            
            def array_reset(arr, **kwargs):
                arr.fill(0)
            
            self.register_pool(
                pool_name,
                np.ndarray,
                factory_func=array_factory,
                reset_func=array_reset,
                max_pool_size=20
            )
    
    def register_pool(self, 
                     name: str,
                     object_class: Type,
                     factory_func: Optional[Callable] = None,
                     reset_func: Optional[Callable] = None,
                     max_pool_size: int = 100) -> None:
        """
        新しいオブジェクトプールを登録
        
        Args:
            name: プール名
            object_class: オブジェクトクラス
            factory_func: オブジェクト生成関数
            reset_func: オブジェクトリセット関数
            max_pool_size: プールの最大サイズ
        """
        if name in self._pools:
            logger.warning(f"プール '{name}' は既に存在します。上書きします。")
        
        self._pools[name] = ObjectPool(
            object_class,
            factory_func,
            reset_func,
            max_pool_size
        )
    
    def acquire(self, pool_name: str, **kwargs) -> Any:
        """
        指定されたプールからオブジェクトを取得
        
        Args:
            pool_name: プール名
            **kwargs: オブジェクト初期化パラメータ
            
        Returns:
            取得したオブジェクト
        """
        if pool_name not in self._pools:
            raise KeyError(f"プール '{pool_name}' が見つかりません")
        
        # メモリ使用率チェック
        self._check_memory_usage()
        
        return self._pools[pool_name].acquire(**kwargs)
    
    def release(self, pool_name: str, obj: Any) -> None:
        """
        オブジェクトをプールに返却
        
        Args:
            pool_name: プール名
            obj: 返却するオブジェクト
        """
        if pool_name not in self._pools:
            return
        
        self._pools[pool_name].release(obj)
    
    def _check_memory_usage(self) -> None:
        """メモリ使用量をチェックし、必要に応じてGCを実行"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        
        # 履歴に記録
        self._memory_usage_history.append({
            'timestamp': datetime.now(),
            'memory_mb': memory_usage_mb,
            'pools': {name: pool.get_stats() for name, pool in self._pools.items()}
        })
        
        # 履歴が大きくなりすぎないように制限
        if len(self._memory_usage_history) > 1000:
            self._memory_usage_history = self._memory_usage_history[-500:]
        
        # メモリ使用率チェック（自動GCが有効な場合のみ）
        usage_ratio = memory_usage_mb / self.memory_limit_mb
        
        if self.auto_gc_enabled and usage_ratio > self._gc_threshold:
            logger.warning(f"メモリ使用率が{usage_ratio:.1%}に達しました。GCを実行します。")
            self._run_garbage_collection()
    
    def _run_garbage_collection(self) -> None:
        """ガベージコレクションを実行"""
        # プールのクリーンアップ
        for pool in self._pools.values():
            # 利用可能なオブジェクトの一部を解放
            available_count = len(pool._available)
            if available_count > 10:
                release_count = available_count // 2
                for _ in range(release_count):
                    if pool._available:
                        obj = pool._available.pop()
                        pool._destroy_object(obj)
                        pool._stats['destroyed'] += 1
        
        # 明示的なガベージコレクション
        gc.collect()
        
        # メモリ使用量を再チェック
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        logger.info(f"GC後のメモリ使用量: {memory_usage_mb:.1f}MB")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        メモリ使用統計を取得
        
        Returns:
            メモリ統計情報
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        
        pool_stats = {}
        total_objects = 0
        
        for name, pool in self._pools.items():
            stats = pool.get_stats()
            pool_stats[name] = stats
            total_objects += stats['available'] + stats['in_use']
        
        return {
            'memory_usage_mb': memory_usage_mb,
            'memory_limit_mb': self.memory_limit_mb,
            'usage_ratio': memory_usage_mb / self.memory_limit_mb,
            'total_objects': total_objects,
            'pools': pool_stats,
            'gc_collections': gc.get_count()
        }
    
    def optimize_memory(self) -> None:
        """メモリ使用を最適化"""
        logger.info("メモリ最適化を開始します...")
        
        # 全プールの統計を取得
        before_stats = self.get_memory_stats()
        
        # 各プールの最適化
        for name, pool in self._pools.items():
            stats = pool.get_stats()
            
            # 利用率が低いプールのサイズを削減
            if stats['available'] > 0 and stats['in_use'] == 0:
                # 完全に未使用のプール
                pool.clear()
            elif stats['available'] > stats['in_use'] * 2:
                # 利用可能数が使用中の2倍以上
                excess = stats['available'] - stats['in_use']
                for _ in range(excess // 2):
                    if pool._available:
                        obj = pool._available.pop()
                        pool._destroy_object(obj)
        
        # ガベージコレクション実行
        gc.collect()
        
        # 最適化後の統計
        after_stats = self.get_memory_stats()
        
        logger.info(
            f"メモリ最適化完了: "
            f"{before_stats['memory_usage_mb']:.1f}MB → "
            f"{after_stats['memory_usage_mb']:.1f}MB"
        )
    
    def clear_all(self) -> None:
        """全てのプールをクリア"""
        for pool in self._pools.values():
            pool.clear()
        
        # 強制的なガベージコレクション
        gc.collect()
    
    def __str__(self) -> str:
        """文字列表現"""
        stats = self.get_memory_stats()
        return (
            f"MemoryPoolManager("
            f"使用: {stats['memory_usage_mb']:.1f}MB/"
            f"{stats['memory_limit_mb']:.1f}MB, "
            f"オブジェクト数: {stats['total_objects']})"
        )


# グローバルメモリプールマネージャーのインスタンス
_global_memory_pool = None


def get_memory_pool() -> MemoryPoolManager:
    """
    グローバルメモリプールマネージャーを取得
    
    Returns:
        メモリプールマネージャーのインスタンス
    """
    global _global_memory_pool
    if _global_memory_pool is None:
        _global_memory_pool = MemoryPoolManager()
    return _global_memory_pool


def reset_memory_pool() -> None:
    """グローバルメモリプールをリセット"""
    global _global_memory_pool
    if _global_memory_pool is not None:
        _global_memory_pool.clear_all()
        _global_memory_pool = None