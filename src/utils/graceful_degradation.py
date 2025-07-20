"""
グレースフルデグラデーション機能

エラーや制限が発生した際に、アプリケーションを完全に停止させるのではなく、
機能を制限した状態で継続実行を可能にする仕組みを提供します。
"""

import sys
import traceback
from typing import Optional, Dict, Any, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    AstroSimException, DependencyError, GPUError, VRAMError,
    MemoryError, PerformanceError, RenderingError
)
from .logging_config import get_logger


class FeatureLevel(Enum):
    """機能レベルの定義"""
    FULL = "full"           # 全機能利用可能
    HIGH = "high"           # 高品質機能
    MEDIUM = "medium"       # 中品質機能
    LOW = "low"             # 基本機能のみ
    MINIMAL = "minimal"     # 最小限の機能
    DISABLED = "disabled"   # 機能無効


@dataclass
class FeatureState:
    """機能の状態管理"""
    name: str
    current_level: FeatureLevel = FeatureLevel.FULL
    available_levels: List[FeatureLevel] = field(default_factory=lambda: list(FeatureLevel))
    error_count: int = 0
    last_error: Optional[Exception] = None
    fallback_reason: Optional[str] = None
    
    def can_downgrade(self) -> bool:
        """さらに品質を下げることができるか"""
        current_index = self.available_levels.index(self.current_level)
        return current_index < len(self.available_levels) - 1
    
    def downgrade(self, reason: str) -> FeatureLevel:
        """品質を一段階下げる"""
        if self.can_downgrade():
            current_index = self.available_levels.index(self.current_level)
            self.current_level = self.available_levels[current_index + 1]
            self.fallback_reason = reason
            
        return self.current_level
    
    def is_disabled(self) -> bool:
        """機能が無効化されているか"""
        return self.current_level == FeatureLevel.DISABLED


class GracefulDegradationManager:
    """
    グレースフルデグラデーション管理クラス
    
    アプリケーション全体の機能レベルを管理し、
    エラー発生時の適切なフォールバック処理を提供します。
    """
    
    def __init__(self):
        """マネージャーの初期化"""
        self.features: Dict[str, FeatureState] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.error_threshold = 3  # エラー発生回数の閾値
        self.logger = get_logger()
        
        # デフォルト機能の初期化
        self._initialize_default_features()
    
    def _initialize_default_features(self) -> None:
        """デフォルト機能の初期化"""
        # 3Dレンダリング機能
        self.register_feature(
            "3d_rendering",
            [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.MEDIUM, 
             FeatureLevel.LOW, FeatureLevel.MINIMAL, FeatureLevel.DISABLED]
        )
        
        # GPU利用機能
        self.register_feature(
            "gpu_acceleration",
            [FeatureLevel.FULL, FeatureLevel.DISABLED]
        )
        
        # 高詳細度モデル
        self.register_feature(
            "high_detail_models",
            [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.MEDIUM, 
             FeatureLevel.LOW, FeatureLevel.DISABLED]
        )
        
        # リアルタイム物理計算
        self.register_feature(
            "realtime_physics",
            [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.MEDIUM, FeatureLevel.DISABLED]
        )
        
        # 軌道線表示
        self.register_feature(
            "orbit_trails",
            [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.DISABLED]
        )
        
        # パーティクル効果
        self.register_feature(
            "particle_effects",
            [FeatureLevel.FULL, FeatureLevel.DISABLED]
        )
        
        # アンチエイリアス
        self.register_feature(
            "antialiasing",
            [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.DISABLED]
        )
    
    def register_feature(self, name: str, available_levels: List[FeatureLevel]) -> None:
        """
        機能を登録
        
        Args:
            name: 機能名
            available_levels: 利用可能なレベルのリスト（高品質から低品質の順）
        """
        self.features[name] = FeatureState(
            name=name,
            available_levels=available_levels,
            current_level=available_levels[0] if available_levels else FeatureLevel.DISABLED
        )
    
    def register_fallback_handler(self, feature_name: str, handler: Callable) -> None:
        """
        フォールバックハンドラーを登録
        
        Args:
            feature_name: 機能名
            handler: フォールバック処理関数
        """
        self.fallback_handlers[feature_name] = handler
    
    def handle_error(self, feature_name: str, error: Exception, 
                    auto_downgrade: bool = True) -> FeatureLevel:
        """
        エラーハンドリングとフォールバック処理
        
        Args:
            feature_name: エラーが発生した機能名
            error: 発生したエラー
            auto_downgrade: 自動的に品質を下げるかどうか
            
        Returns:
            新しい機能レベル
        """
        if feature_name not in self.features:
            self.logger.warning(f"未登録の機能でエラーが発生: {feature_name}")
            return FeatureLevel.DISABLED
        
        feature = self.features[feature_name]
        feature.error_count += 1
        feature.last_error = error
        
        # エラーの分類と対応
        reason = self._classify_error(error)
        
        self.logger.error(
            f"機能 '{feature_name}' でエラーが発生: {reason}",
            exception=error,
            feature=feature_name,
            error_count=feature.error_count
        )
        
        # 自動ダウングレードの判定
        if auto_downgrade and (feature.error_count >= self.error_threshold or 
                              self._is_critical_error(error)):
            if feature.can_downgrade():
                old_level = feature.current_level
                new_level = feature.downgrade(reason)
                
                self.logger.warning(
                    f"機能 '{feature_name}' を {old_level.value} から {new_level.value} にダウングレード: {reason}"
                )
                
                # フォールバックハンドラーの実行
                self._execute_fallback_handler(feature_name, new_level, error)
                
                return new_level
            else:
                # これ以上ダウングレードできない場合
                feature.current_level = FeatureLevel.DISABLED
                self.logger.critical(f"機能 '{feature_name}' を無効化しました: {reason}")
                return FeatureLevel.DISABLED
        
        return feature.current_level
    
    def _classify_error(self, error: Exception) -> str:
        """エラーの分類"""
        if isinstance(error, GPUError):
            return "GPU関連エラー"
        elif isinstance(error, VRAMError):
            return "VRAM不足"
        elif isinstance(error, MemoryError):
            return "メモリ不足"
        elif isinstance(error, DependencyError):
            return "依存関係エラー"
        elif isinstance(error, PerformanceError):
            return "パフォーマンス問題"
        elif isinstance(error, RenderingError):
            return "レンダリングエラー"
        else:
            return f"予期しないエラー: {type(error).__name__}"
    
    def _is_critical_error(self, error: Exception) -> bool:
        """重要なエラーかどうかの判定"""
        critical_errors = (GPUError, VRAMError, DependencyError)
        return isinstance(error, critical_errors)
    
    def _execute_fallback_handler(self, feature_name: str, new_level: FeatureLevel, 
                                 error: Exception) -> None:
        """フォールバックハンドラーの実行"""
        if feature_name in self.fallback_handlers:
            try:
                handler = self.fallback_handlers[feature_name]
                handler(new_level, error)
            except Exception as handler_error:
                self.logger.error(
                    f"フォールバックハンドラーでエラーが発生: {feature_name}",
                    exception=handler_error
                )
    
    def get_feature_level(self, feature_name: str) -> FeatureLevel:
        """
        機能の現在のレベルを取得
        
        Args:
            feature_name: 機能名
            
        Returns:
            現在の機能レベル
        """
        if feature_name not in self.features:
            return FeatureLevel.DISABLED
        
        return self.features[feature_name].current_level
    
    def is_feature_available(self, feature_name: str, min_level: FeatureLevel = FeatureLevel.LOW) -> bool:
        """
        機能が利用可能かどうかをチェック
        
        Args:
            feature_name: 機能名
            min_level: 最小必要レベル
            
        Returns:
            利用可能かどうか
        """
        current_level = self.get_feature_level(feature_name)
        
        if current_level == FeatureLevel.DISABLED:
            return False
        
        # レベルの順序を確認（FULLが最高、DISABLEDが最低）
        level_order = [FeatureLevel.FULL, FeatureLevel.HIGH, FeatureLevel.MEDIUM, 
                      FeatureLevel.LOW, FeatureLevel.MINIMAL, FeatureLevel.DISABLED]
        
        try:
            current_index = level_order.index(current_level)
            min_index = level_order.index(min_level)
            return current_index <= min_index
        except ValueError:
            return False
    
    def force_feature_level(self, feature_name: str, level: FeatureLevel, reason: str = "手動設定") -> None:
        """
        機能レベルを強制的に設定
        
        Args:
            feature_name: 機能名
            level: 設定するレベル
            reason: 設定理由
        """
        if feature_name in self.features:
            feature = self.features[feature_name]
            old_level = feature.current_level
            feature.current_level = level
            feature.fallback_reason = reason
            
            self.logger.info(
                f"機能 '{feature_name}' のレベルを {old_level.value} から {level.value} に変更: {reason}"
            )
    
    def get_degradation_report(self) -> Dict[str, Any]:
        """
        現在のデグラデーション状況のレポートを取得
        
        Returns:
            デグラデーション状況の辞書
        """
        report = {
            "features": {},
            "summary": {
                "total_features": len(self.features),
                "degraded_features": 0,
                "disabled_features": 0
            }
        }
        
        for name, feature in self.features.items():
            is_degraded = feature.current_level != feature.available_levels[0]
            is_disabled = feature.is_disabled()
            
            report["features"][name] = {
                "current_level": feature.current_level.value,
                "original_level": feature.available_levels[0].value,
                "is_degraded": is_degraded,
                "is_disabled": is_disabled,
                "error_count": feature.error_count,
                "fallback_reason": feature.fallback_reason
            }
            
            if is_degraded:
                report["summary"]["degraded_features"] += 1
            if is_disabled:
                report["summary"]["disabled_features"] += 1
        
        return report
    
    def reset_feature(self, feature_name: str) -> None:
        """
        機能を初期状態にリセット
        
        Args:
            feature_name: 機能名
        """
        if feature_name in self.features:
            feature = self.features[feature_name]
            feature.current_level = feature.available_levels[0]
            feature.error_count = 0
            feature.last_error = None
            feature.fallback_reason = None
            
            self.logger.info(f"機能 '{feature_name}' を初期状態にリセットしました")
    
    def reset_all_features(self) -> None:
        """全機能を初期状態にリセット"""
        for feature_name in self.features.keys():
            self.reset_feature(feature_name)
        
        self.logger.info("全機能を初期状態にリセットしました")


# グローバルマネージャーインスタンス
_global_manager: Optional[GracefulDegradationManager] = None


def get_degradation_manager() -> GracefulDegradationManager:
    """
    グローバルデグラデーションマネージャーの取得
    
    Returns:
        グローバルマネージャーインスタンス
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = GracefulDegradationManager()
    
    return _global_manager


def with_graceful_degradation(feature_name: str, min_level: FeatureLevel = FeatureLevel.LOW):
    """
    グレースフルデグラデーション付きで関数を実行するデコレータ
    
    Args:
        feature_name: 機能名
        min_level: 最小必要レベル
        
    Returns:
        デコレータ関数
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            manager = get_degradation_manager()
            
            # 機能が利用可能かチェック
            if not manager.is_feature_available(feature_name, min_level):
                raise FeatureUnavailableError(
                    f"機能 '{feature_name}' は現在利用できません（最小レベル: {min_level.value}）"
                )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # エラー発生時のハンドリング
                new_level = manager.handle_error(feature_name, e)
                
                # 機能が完全に無効化された場合は例外を再発生
                if new_level == FeatureLevel.DISABLED:
                    raise
                
                # ダウングレード後に再試行（オプション）
                # この実装では再試行しないが、必要に応じて追加可能
                raise
        
        return wrapper
    return decorator


class FeatureUnavailableError(AstroSimException):
    """機能が利用できない場合のエラー"""
    pass


# 便利関数

def check_gpu_availability() -> bool:
    """GPU利用可能性のチェック"""
    try:
        import vispy
        from vispy import app
        
        # テスト環境ではバックエンドが利用できない場合があるのでスキップ
        if hasattr(vispy, '_testing') or not hasattr(app, 'Canvas'):
            return False
        
        # 簡単なテスト用キャンバスを作成
        canvas = app.Canvas(size=(100, 100), show=False)
        canvas.close()
        return True
        
    except Exception as e:
        manager = get_degradation_manager()
        manager.handle_error("gpu_acceleration", GPUError("GPU利用不可", cause=e))
        return False


def check_memory_availability(required_mb: float) -> bool:
    """メモリ利用可能性のチェック"""
    try:
        import psutil
        
        available_memory = psutil.virtual_memory().available / (1024 * 1024)
        return available_memory >= required_mb
        
    except Exception:
        return False


def adaptive_quality_settings(target_fps: float = 30.0) -> Dict[str, Any]:
    """
    パフォーマンスに基づく適応的品質設定
    
    Args:
        target_fps: 目標FPS
        
    Returns:
        推奨品質設定
    """
    manager = get_degradation_manager()
    
    settings = {
        "detail_level": manager.get_feature_level("high_detail_models"),
        "use_antialiasing": manager.is_feature_available("antialiasing"),
        "use_particles": manager.is_feature_available("particle_effects"),
        "use_orbit_trails": manager.is_feature_available("orbit_trails"),
        "gpu_acceleration": manager.is_feature_available("gpu_acceleration")
    }
    
    return settings