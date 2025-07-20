"""
AstroSim統合ログシステム

アプリケーション全体で統一されたログ出力機能を提供します。
エラーレベル別のファイル分割、デバッグモード、パフォーマンス監視などを含みます。
"""

import logging
import logging.handlers
import os
import time
import functools
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from .exceptions import AstroSimException, get_error_level, ErrorLevel


class AstroSimLogger:
    """
    AstroSimアプリケーション用の統合ログシステム
    
    機能:
    - エラーレベル別ファイル分割
    - デバッグモード切替
    - パフォーマンス監視
    - 自動ログディレクトリ作成
    - ログローテーション
    """
    
    def __init__(self, log_dir: str = "logs", app_name: str = "AstroSim"):
        """
        ログシステムの初期化
        
        Args:
            log_dir: ログディレクトリパス
            app_name: アプリケーション名
        """
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.debug_mode = False
        
        # ログディレクトリの作成
        self._ensure_log_directory()
        
        # ロガーの設定
        self._setup_loggers()
        
        # パフォーマンス監視
        self.performance_data: Dict[str, Dict[str, Any]] = {}
        
    def _ensure_log_directory(self) -> None:
        """ログディレクトリの存在確認・作成"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # サブディレクトリの作成
            (self.log_dir / "errors").mkdir(exist_ok=True)
            (self.log_dir / "debug").mkdir(exist_ok=True)
            (self.log_dir / "performance").mkdir(exist_ok=True)
            
        except Exception as e:
            # ログディレクトリ作成に失敗した場合はカレントディレクトリを使用
            print(f"警告: ログディレクトリの作成に失敗しました: {e}")
            self.log_dir = Path(".")
    
    def _setup_loggers(self) -> None:
        """各種ロガーの設定"""
        # メインロガー
        self.main_logger = self._create_logger(
            "astrosim.main",
            self.log_dir / f"{self.app_name}.log",
            logging.INFO
        )
        
        # エラー専用ロガー
        self.error_logger = self._create_logger(
            "astrosim.error",
            self.log_dir / "errors" / "error.log",
            logging.ERROR
        )
        
        # デバッグ専用ロガー
        self.debug_logger = self._create_logger(
            "astrosim.debug",
            self.log_dir / "debug" / "debug.log",
            logging.DEBUG
        )
        
        # パフォーマンス専用ロガー
        self.performance_logger = self._create_logger(
            "astrosim.performance",
            self.log_dir / "performance" / "performance.log",
            logging.INFO
        )
        
        # コンソールロガー
        self.console_logger = self._create_console_logger()
    
    def _create_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """
        個別ロガーの作成
        
        Args:
            name: ロガー名
            log_file: ログファイルパス
            level: ログレベル
            
        Returns:
            設定済みロガー
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 既存のハンドラーをクリア
        logger.handlers.clear()
        
        # ファイルハンドラー（ローテーション付き）
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.propagate = False
        
        return logger
    
    def _create_console_logger(self) -> logging.Logger:
        """コンソール出力用ロガーの作成"""
        logger = logging.getLogger("astrosim.console")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        
        # 簡潔なフォーマッター
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.propagate = False
        
        return logger
    
    def set_debug_mode(self, enabled: bool) -> None:
        """
        デバッグモードの設定
        
        Args:
            enabled: デバッグモード有効フラグ
        """
        self.debug_mode = enabled
        level = logging.DEBUG if enabled else logging.INFO
        
        # 全ロガーのレベルを更新
        self.main_logger.setLevel(level)
        self.console_logger.setLevel(level)
        
        if enabled:
            self.info("デバッグモードが有効になりました")
        else:
            self.info("デバッグモードが無効になりました")
    
    def info(self, message: str, **kwargs) -> None:
        """情報ログ出力"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """警告ログ出力"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """エラーログ出力"""
        if exception:
            # 例外情報を含む詳細ログ
            error_details = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc(),
                **kwargs
            }
            self.error_logger.error(f"{message} - {error_details}")
        
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """重要エラーログ出力"""
        if exception:
            error_details = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc(),
                **kwargs
            }
            self.error_logger.critical(f"{message} - {error_details}")
        
        self._log(logging.CRITICAL, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """デバッグログ出力"""
        if self.debug_mode:
            self.debug_logger.debug(f"{message} - {kwargs}" if kwargs else message)
            self._log(logging.DEBUG, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """共通ログ出力処理"""
        # メインログファイルに出力
        self.main_logger.log(level, f"{message} - {kwargs}" if kwargs else message)
        
        # コンソールに出力（レベルに応じて）
        if level >= self.console_logger.level:
            self.console_logger.log(level, message)
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        例外の詳細ログ出力
        
        Args:
            exception: 発生した例外
            context: 追加コンテキスト情報
        """
        context = context or {}
        
        # エラーレベルの決定
        error_level = get_error_level(exception)
        
        # AstroSim例外の場合は詳細情報を取得
        if isinstance(exception, AstroSimException):
            details = exception.to_dict()
            # 'message' キーを 'exception_message' に変更して重複を避ける
            if 'message' in details:
                details['exception_message'] = details.pop('message')
            details.update(context)
        else:
            details = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc(),
                **context
            }
        
        # レベルに応じてログ出力
        if error_level == ErrorLevel.CRITICAL:
            self.critical(f"重要エラーが発生しました: {exception}", **details)
        elif error_level == ErrorLevel.ERROR:
            self.error(f"エラーが発生しました: {exception}", **details)
        elif error_level == ErrorLevel.WARNING:
            self.warning(f"警告: {exception}", **details)
        else:
            self.info(f"情報: {exception}", **details)
    
    def log_performance(self, operation: str, duration: float, **metrics) -> None:
        """
        パフォーマンス情報のログ出力
        
        Args:
            operation: 操作名
            duration: 実行時間（秒）
            **metrics: 追加メトリクス
        """
        performance_data = {
            "operation": operation,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            **metrics
        }
        
        self.performance_logger.info(f"Performance: {performance_data}")
        
        # パフォーマンスデータの蓄積
        if operation not in self.performance_data:
            self.performance_data[operation] = {
                "count": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0
            }
        
        data = self.performance_data[operation]
        data["count"] += 1
        data["total_duration"] += duration
        data["min_duration"] = min(data["min_duration"], duration)
        data["max_duration"] = max(data["max_duration"], duration)
        data["avg_duration"] = data["total_duration"] / data["count"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス統計の取得"""
        return dict(self.performance_data)
    
    def log_system_info(self) -> None:
        """システム情報のログ出力"""
        import platform
        import psutil
        
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_free_gb": psutil.disk_usage('/').free / (1024**3)
        }
        
        self.info("システム情報", **system_info)


def performance_monitor(operation_name: Optional[str] = None):
    """
    関数の実行時間を監視するデコレータ
    
    Args:
        operation_name: 操作名（未指定の場合は関数名を使用）
        
    Returns:
        デコレータ関数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # ログ出力
                op_name = operation_name or func.__name__
                logger = get_logger()
                logger.log_performance(op_name, duration, status="success")
                
                return result
                
            except Exception as e:
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # エラー時もパフォーマンスログを出力
                op_name = operation_name or func.__name__
                logger = get_logger()
                logger.log_performance(op_name, duration, status="error", error=str(e))
                
                raise
        
        return wrapper
    return decorator


# グローバルロガーインスタンス
_global_logger: Optional[AstroSimLogger] = None


def initialize_logging(log_dir: str = "logs", debug_mode: bool = False) -> AstroSimLogger:
    """
    グローバルログシステムの初期化
    
    Args:
        log_dir: ログディレクトリ
        debug_mode: デバッグモード
        
    Returns:
        初期化されたロガー
    """
    global _global_logger
    
    _global_logger = AstroSimLogger(log_dir)
    _global_logger.set_debug_mode(debug_mode)
    _global_logger.log_system_info()
    
    return _global_logger


def get_logger() -> AstroSimLogger:
    """
    グローバルロガーの取得
    
    Returns:
        グローバルロガーインスタンス
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = initialize_logging()
    
    return _global_logger


def log_exception_with_context(operation: str, **context):
    """
    コンテキスト付きで例外をログ出力するデコレータ
    
    Args:
        operation: 操作名
        **context: 追加コンテキスト
        
    Returns:
        デコレータ関数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = get_logger()
                error_context = {
                    "function": func.__name__,
                    "operation": operation,
                    **context
                }
                logger.log_exception(e, error_context)
                raise
        
        return wrapper
    return decorator