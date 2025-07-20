"""
AstroSimカスタム例外クラス体系

アプリケーション全体で使用される統一的な例外クラスを定義し、
エラーの分類と適切な処理を可能にします。
"""

from typing import Optional, Dict, Any


class AstroSimException(Exception):
    """
    AstroSimアプリケーションの基底例外クラス
    
    全てのAstroSim固有の例外はこのクラスを継承します。
    エラーメッセージ、エラーコード、追加情報を保持できます。
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        """
        カスタム例外の初期化
        
        Args:
            message: ユーザー向けエラーメッセージ
            error_code: システム内部でのエラー識別コード
            details: エラーの詳細情報（デバッグ用）
            cause: 原因となった元の例外
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """文字列表現"""
        result = f"{self.error_code}: {self.message}"
        if self.cause:
            result += f" (原因: {self.cause})"
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式での情報取得（ログ出力用）"""
        return {
            "exception_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


# === シミュレーション関連例外 ===

class SimulationError(AstroSimException):
    """シミュレーション処理に関する例外の基底クラス"""
    pass


class PhysicsCalculationError(SimulationError):
    """物理計算エラー"""
    pass


class OrbitCalculationError(PhysicsCalculationError):
    """軌道計算エラー"""
    pass


class TimeManagementError(SimulationError):
    """時間管理エラー"""
    pass


class ConvergenceError(PhysicsCalculationError):
    """数値計算の収束エラー"""
    pass


# === 可視化関連例外 ===

class VisualizationError(AstroSimException):
    """可視化処理に関する例外の基底クラス"""
    pass


class RenderingError(VisualizationError):
    """レンダリングエラー"""
    pass


class GPUError(VisualizationError):
    """GPU関連エラー"""
    pass


class OpenGLError(GPUError):
    """OpenGL関連エラー"""
    pass


class ShaderError(OpenGLError):
    """シェーダーコンパイル・実行エラー"""
    pass


class VRAMError(GPUError):
    """VRAM不足エラー"""
    pass


class CameraError(VisualizationError):
    """カメラ制御エラー"""
    pass


class SceneError(VisualizationError):
    """3Dシーン管理エラー"""
    pass


# === UI関連例外 ===

class UIError(AstroSimException):
    """ユーザーインターフェース関連例外の基底クラス"""
    pass


class WindowError(UIError):
    """ウィンドウ管理エラー"""
    pass


class WidgetError(UIError):
    """ウィジェット関連エラー"""
    pass


class EventHandlingError(UIError):
    """イベント処理エラー"""
    pass


# === データ関連例外 ===

class DataError(AstroSimException):
    """データ処理に関する例外の基底クラス"""
    pass


class DataLoadException(DataError):
    """データ読み込みエラー（既存の例外を統合）"""
    pass


class DataSaveError(DataError):
    """データ保存エラー"""
    pass


class DataValidationError(DataError):
    """データ検証エラー"""
    pass


class ConfigurationError(DataError):
    """設定ファイルエラー"""
    pass


class PlanetDataError(DataError):
    """惑星データ関連エラー"""
    pass


# === システム関連例外 ===

class SystemError(AstroSimException):
    """システム関連例外の基底クラス"""
    pass


class DependencyError(SystemError):
    """依存関係エラー"""
    pass


class MemoryError(SystemError):
    """メモリ関連エラー"""
    pass


class PerformanceError(SystemError):
    """パフォーマンス関連エラー"""
    pass


class ResourceError(SystemError):
    """リソース不足エラー"""
    pass


# === ユーティリティ関数 ===

def wrap_exception(func):
    """
    関数をラップして、一般的な例外をAstroSim例外に変換するデコレータ
    
    Args:
        func: ラップする関数
        
    Returns:
        ラップされた関数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AstroSimException:
            # AstroSim例外はそのまま通す
            raise
        except ValueError as e:
            raise DataValidationError(f"値の検証エラー: {e}", cause=e)
        except FileNotFoundError as e:
            raise DataLoadException(f"ファイルが見つかりません: {e}", cause=e)
        except MemoryError as e:
            raise SystemError(f"メモリ不足: {e}", cause=e)
        except ImportError as e:
            raise DependencyError(f"依存関係エラー: {e}", cause=e)
        except Exception as e:
            # その他の予期しない例外
            raise AstroSimException(f"予期しないエラー: {e}", cause=e)
    
    return wrapper


def create_error_context(operation: str, **context) -> Dict[str, Any]:
    """
    エラーコンテキスト情報を作成
    
    Args:
        operation: 実行していた操作名
        **context: 追加のコンテキスト情報
        
    Returns:
        エラーコンテキスト辞書
    """
    import time
    import platform
    
    return {
        "operation": operation,
        "timestamp": time.time(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        **context
    }


def format_user_friendly_message(exception: AstroSimException, 
                                include_technical: bool = False) -> str:
    """
    ユーザーフレンドリーなエラーメッセージを生成
    
    Args:
        exception: AstroSim例外
        include_technical: 技術的詳細を含めるかどうか
        
    Returns:
        フォーマットされたメッセージ
    """
    message = exception.message
    
    # エラータイプに応じた解決方法の提示
    solutions = {
        "DependencyError": "必要なライブラリがインストールされていません。requirements.txtを確認してください。",
        "GPUError": "グラフィックスの処理でエラーが発生しました。ドライバーを更新するか、設定を変更してください。",
        "DataLoadException": "データファイルの読み込みに失敗しました。ファイルの存在と形式を確認してください。",
        "MemoryError": "メモリが不足しています。他のアプリケーションを終了するか、設定を変更してください。",
        "PhysicsCalculationError": "物理計算でエラーが発生しました。パラメータを確認してください。"
    }
    
    solution = solutions.get(exception.__class__.__name__)
    if solution:
        message += f"\n\n解決方法: {solution}"
    
    if include_technical and exception.details:
        message += f"\n\n技術的詳細: {exception.details}"
    
    return message


# エラーレベル定義
class ErrorLevel:
    """エラーレベル定数"""
    CRITICAL = "CRITICAL"  # アプリケーション停止
    ERROR = "ERROR"        # 機能停止
    WARNING = "WARNING"    # 警告
    INFO = "INFO"          # 情報
    DEBUG = "DEBUG"        # デバッグ


def get_error_level(exception: Exception) -> str:
    """
    例外に応じたエラーレベルを決定
    
    Args:
        exception: 発生した例外
        
    Returns:
        エラーレベル
    """
    # より具体的な例外から先にチェック（継承関係を考慮）
    warning_exceptions = (PerformanceError, ConfigurationError)
    critical_errors = (DependencyError, SystemError, GPUError)
    error_exceptions = (SimulationError, VisualizationError, DataError, ValueError, TypeError, RuntimeError)
    
    if isinstance(exception, warning_exceptions):
        return ErrorLevel.WARNING
    elif isinstance(exception, critical_errors):
        return ErrorLevel.CRITICAL
    elif isinstance(exception, error_exceptions):
        return ErrorLevel.ERROR
    else:
        return ErrorLevel.INFO