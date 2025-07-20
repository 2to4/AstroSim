"""
AstroSimカスタム例外体系のテスト

exceptions.pyのカスタム例外クラス、ユーティリティ関数、
エラーレベル決定機能を包括的にテストします。
"""

import pytest
import platform
import time
from unittest.mock import patch, Mock

# プロジェクトルートを追加
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.exceptions import (
    # 基底例外
    AstroSimException,
    
    # シミュレーション関連例外
    SimulationError, PhysicsCalculationError, OrbitCalculationError,
    TimeManagementError, ConvergenceError,
    
    # 可視化関連例外
    VisualizationError, RenderingError, GPUError, OpenGLError,
    ShaderError, VRAMError, CameraError, SceneError,
    
    # UI関連例外
    UIError, WindowError, WidgetError, EventHandlingError,
    
    # データ関連例外
    DataError, DataLoadException, DataSaveError, DataValidationError,
    ConfigurationError, PlanetDataError,
    
    # システム関連例外
    SystemError, DependencyError, MemoryError, PerformanceError,
    ResourceError,
    
    # ユーティリティ関数
    wrap_exception, create_error_context, format_user_friendly_message,
    ErrorLevel, get_error_level
)


class TestAstroSimException:
    """AstroSimException基底クラスのテスト"""
    
    def test_basic_initialization(self):
        """基本的な初期化テスト"""
        exc = AstroSimException("テストエラーメッセージ")
        
        assert exc.message == "テストエラーメッセージ"
        assert exc.error_code == "AstroSimException"
        assert exc.details == {}
        assert exc.cause is None
    
    def test_full_initialization(self):
        """全パラメータ指定での初期化テスト"""
        details = {"param1": "value1", "param2": 123}
        cause = ValueError("原因となる例外")
        
        exc = AstroSimException(
            message="詳細エラーメッセージ",
            error_code="CUSTOM_ERROR",
            details=details,
            cause=cause
        )
        
        assert exc.message == "詳細エラーメッセージ"
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == details
        assert exc.cause == cause
    
    def test_string_representation(self):
        """文字列表現のテスト"""
        exc = AstroSimException("テストメッセージ", error_code="TEST_CODE")
        assert str(exc) == "TEST_CODE: テストメッセージ"
        
        # 原因がある場合
        cause = ValueError("原因")
        exc_with_cause = AstroSimException("テスト", cause=cause)
        assert "原因: 原因" in str(exc_with_cause)
    
    def test_to_dict_method(self):
        """to_dict メソッドのテスト"""
        details = {"key": "value"}
        cause = RuntimeError("原因エラー")
        
        exc = AstroSimException(
            "テストメッセージ",
            error_code="TEST",
            details=details,
            cause=cause
        )
        
        result = exc.to_dict()
        
        assert result["exception_type"] == "AstroSimException"
        assert result["error_code"] == "TEST"
        assert result["message"] == "テストメッセージ"
        assert result["details"] == details
        assert result["cause"] == "原因エラー"
    
    def test_to_dict_without_cause(self):
        """原因がない場合のto_dictテスト"""
        exc = AstroSimException("テスト")
        result = exc.to_dict()
        
        assert result["cause"] is None


class TestExceptionHierarchy:
    """例外階層のテスト"""
    
    def test_simulation_exceptions(self):
        """シミュレーション関連例外の階層テスト"""
        assert issubclass(SimulationError, AstroSimException)
        assert issubclass(PhysicsCalculationError, SimulationError)
        assert issubclass(OrbitCalculationError, PhysicsCalculationError)
        assert issubclass(TimeManagementError, SimulationError)
        assert issubclass(ConvergenceError, PhysicsCalculationError)
    
    def test_visualization_exceptions(self):
        """可視化関連例外の階層テスト"""
        assert issubclass(VisualizationError, AstroSimException)
        assert issubclass(RenderingError, VisualizationError)
        assert issubclass(GPUError, VisualizationError)
        assert issubclass(OpenGLError, GPUError)
        assert issubclass(ShaderError, OpenGLError)
        assert issubclass(VRAMError, GPUError)
        assert issubclass(CameraError, VisualizationError)
        assert issubclass(SceneError, VisualizationError)
    
    def test_ui_exceptions(self):
        """UI関連例外の階層テスト"""
        assert issubclass(UIError, AstroSimException)
        assert issubclass(WindowError, UIError)
        assert issubclass(WidgetError, UIError)
        assert issubclass(EventHandlingError, UIError)
    
    def test_data_exceptions(self):
        """データ関連例外の階層テスト"""
        assert issubclass(DataError, AstroSimException)
        assert issubclass(DataLoadException, DataError)
        assert issubclass(DataSaveError, DataError)
        assert issubclass(DataValidationError, DataError)
        assert issubclass(ConfigurationError, DataError)
        assert issubclass(PlanetDataError, DataError)
    
    def test_system_exceptions(self):
        """システム関連例外の階層テスト"""
        assert issubclass(SystemError, AstroSimException)
        assert issubclass(DependencyError, SystemError)
        assert issubclass(MemoryError, SystemError)
        assert issubclass(PerformanceError, SystemError)
        assert issubclass(ResourceError, SystemError)


class TestWrapExceptionDecorator:
    """wrap_exception デコレータのテスト"""
    
    def test_successful_execution(self):
        """正常実行時のテスト"""
        @wrap_exception
        def test_function(x, y):
            return x + y
        
        result = test_function(1, 2)
        assert result == 3
    
    def test_value_error_wrapping(self):
        """ValueError の変換テスト"""
        @wrap_exception
        def test_function():
            raise ValueError("無効な値")
        
        with pytest.raises(DataValidationError) as exc_info:
            test_function()
        
        assert "値の検証エラー" in str(exc_info.value)
        assert isinstance(exc_info.value.cause, ValueError)
    
    def test_file_not_found_error_wrapping(self):
        """FileNotFoundError の変換テスト"""
        @wrap_exception
        def test_function():
            raise FileNotFoundError("ファイルなし")
        
        with pytest.raises(DataLoadException) as exc_info:
            test_function()
        
        assert "ファイルが見つかりません" in str(exc_info.value)
    
    def test_memory_error_wrapping(self):
        """MemoryError の変換テスト"""
        @wrap_exception
        def test_function():
            raise MemoryError("メモリ不足")
        
        with pytest.raises(SystemError) as exc_info:
            test_function()
        
        assert "メモリ不足" in str(exc_info.value)
    
    def test_import_error_wrapping(self):
        """ImportError の変換テスト"""
        @wrap_exception
        def test_function():
            raise ImportError("モジュールなし")
        
        with pytest.raises(DependencyError) as exc_info:
            test_function()
        
        assert "依存関係エラー" in str(exc_info.value)
    
    def test_generic_exception_wrapping(self):
        """一般的な例外の変換テスト"""
        @wrap_exception
        def test_function():
            raise RuntimeError("予期しないエラー")
        
        with pytest.raises(AstroSimException) as exc_info:
            test_function()
        
        assert "予期しないエラー" in str(exc_info.value)
    
    def test_astrosim_exception_pass_through(self):
        """AstroSim例外はそのまま通すテスト"""
        @wrap_exception
        def test_function():
            raise SimulationError("シミュレーションエラー")
        
        with pytest.raises(SimulationError):
            test_function()


class TestCreateErrorContext:
    """create_error_context 関数のテスト"""
    
    @patch('time.time', return_value=1234567890.0)
    @patch('platform.system', return_value='Darwin')
    @patch('platform.python_version', return_value='3.9.0')
    def test_basic_context_creation(self, mock_python_version, mock_system, mock_time):
        """基本的なコンテキスト作成テスト"""
        context = create_error_context("test_operation")
        
        assert context["operation"] == "test_operation"
        assert context["timestamp"] == 1234567890.0
        assert context["platform"] == "Darwin"
        assert context["python_version"] == "3.9.0"
    
    def test_context_with_additional_info(self):
        """追加情報付きコンテキスト作成テスト"""
        context = create_error_context(
            "complex_operation",
            file_name="test.py",
            line_number=42,
            user_id=123
        )
        
        assert context["operation"] == "complex_operation"
        assert context["file_name"] == "test.py"
        assert context["line_number"] == 42
        assert context["user_id"] == 123
        assert "timestamp" in context
        assert "platform" in context
        assert "python_version" in context


class TestFormatUserFriendlyMessage:
    """format_user_friendly_message 関数のテスト"""
    
    def test_basic_message_formatting(self):
        """基本的なメッセージフォーマットテスト"""
        exc = AstroSimException("基本エラーメッセージ")
        message = format_user_friendly_message(exc)
        
        assert message == "基本エラーメッセージ"
    
    def test_dependency_error_with_solution(self):
        """DependencyError の解決方法付きメッセージテスト"""
        exc = DependencyError("ライブラリが見つかりません")
        message = format_user_friendly_message(exc)
        
        assert "ライブラリが見つかりません" in message
        assert "requirements.txt" in message
        assert "解決方法:" in message
    
    def test_gpu_error_with_solution(self):
        """GPUError の解決方法付きメッセージテスト"""
        exc = GPUError("グラフィックスエラー")
        message = format_user_friendly_message(exc)
        
        assert "グラフィックスエラー" in message
        assert "ドライバー" in message
    
    def test_data_load_error_with_solution(self):
        """DataLoadException の解決方法付きメッセージテスト"""
        exc = DataLoadException("ファイル読み込みエラー")
        message = format_user_friendly_message(exc)
        
        assert "ファイル読み込みエラー" in message
        assert "ファイルの存在" in message
    
    def test_message_with_technical_details(self):
        """技術的詳細を含むメッセージテスト"""
        details = {"stack_trace": "line 1\\nline 2", "variable": "test_value"}
        exc = AstroSimException("エラー", details=details)
        
        message = format_user_friendly_message(exc, include_technical=True)
        
        assert "エラー" in message
        assert "技術的詳細:" in message
        assert str(details) in message
    
    def test_message_without_technical_details(self):
        """技術的詳細を含まないメッセージテスト"""
        details = {"debug": "info"}
        exc = AstroSimException("エラー", details=details)
        
        message = format_user_friendly_message(exc, include_technical=False)
        
        assert "エラー" in message
        assert "技術的詳細:" not in message
    
    def test_unknown_exception_type(self):
        """未知の例外タイプのテスト"""
        exc = AstroSimException("未知のエラー")
        message = format_user_friendly_message(exc)
        
        assert message == "未知のエラー"  # 解決方法は追加されない


class TestErrorLevel:
    """ErrorLevel クラスのテスト"""
    
    def test_error_level_constants(self):
        """エラーレベル定数のテスト"""
        assert ErrorLevel.CRITICAL == "CRITICAL"
        assert ErrorLevel.ERROR == "ERROR"
        assert ErrorLevel.WARNING == "WARNING"
        assert ErrorLevel.INFO == "INFO"
        assert ErrorLevel.DEBUG == "DEBUG"


class TestGetErrorLevel:
    """get_error_level 関数のテスト"""
    
    def test_critical_error_level(self):
        """CRITICAL レベルエラーのテスト"""
        exceptions = [
            DependencyError("依存関係エラー"),
            SystemError("システムエラー"),
            GPUError("GPUエラー")
        ]
        
        for exc in exceptions:
            assert get_error_level(exc) == ErrorLevel.CRITICAL
    
    def test_error_level_errors(self):
        """ERROR レベルエラーのテスト"""
        exceptions = [
            SimulationError("シミュレーションエラー"),
            VisualizationError("可視化エラー"),
            DataError("データエラー"),
            ValueError("値エラー"),
            TypeError("型エラー"),
            RuntimeError("実行時エラー")
        ]
        
        for exc in exceptions:
            assert get_error_level(exc) == ErrorLevel.ERROR
    
    def test_warning_level_errors(self):
        """WARNING レベルエラーのテスト"""
        exceptions = [
            PerformanceError("パフォーマンスエラー"),
            ConfigurationError("設定エラー")
        ]
        
        for exc in exceptions:
            assert get_error_level(exc) == ErrorLevel.WARNING
    
    def test_info_level_errors(self):
        """INFO レベルエラーのテスト"""
        exceptions = [
            Exception("一般的な例外"),
            KeyError("キーエラー"),
            IndexError("インデックスエラー")
        ]
        
        for exc in exceptions:
            assert get_error_level(exc) == ErrorLevel.INFO
    
    def test_nested_exception_levels(self):
        """入れ子になった例外のレベルテスト"""
        # PhysicsCalculationError は SimulationError を継承
        physics_error = PhysicsCalculationError("物理計算エラー")
        assert get_error_level(physics_error) == ErrorLevel.ERROR
        
        # OrbitCalculationError は PhysicsCalculationError を継承
        orbit_error = OrbitCalculationError("軌道計算エラー")
        assert get_error_level(orbit_error) == ErrorLevel.ERROR


class TestExceptionIntegration:
    """例外体系の統合テスト"""
    
    def test_exception_chain_creation(self):
        """例外チェーンの作成テスト"""
        try:
            try:
                raise ValueError("元の値エラー")
            except ValueError as e:
                raise DataValidationError("データ検証エラー", cause=e)
        except DataValidationError as exc:
            assert exc.message == "データ検証エラー"
            assert isinstance(exc.cause, ValueError)
            assert str(exc.cause) == "元の値エラー"
    
    def test_exception_with_context(self):
        """コンテキスト付き例外の作成テスト"""
        context = create_error_context(
            "planet_calculation",
            planet_name="Earth",
            time_step=0.1
        )
        
        exc = PhysicsCalculationError(
            "惑星計算でエラーが発生しました",
            error_code="PHYSICS_001",
            details=context
        )
        
        assert exc.error_code == "PHYSICS_001"
        assert exc.details["operation"] == "planet_calculation"
        assert exc.details["planet_name"] == "Earth"
        assert exc.details["time_step"] == 0.1
    
    def test_exception_serialization(self):
        """例外のシリアライゼーションテスト"""
        exc = SimulationError(
            "シミュレーションが停止しました",
            error_code="SIM_001",
            details={"step": 1000, "reason": "convergence_failure"}
        )
        
        serialized = exc.to_dict()
        
        # シリアライズされた情報から詳細を再現できることを確認
        assert serialized["exception_type"] == "SimulationError"
        assert serialized["error_code"] == "SIM_001"
        assert serialized["message"] == "シミュレーションが停止しました"
        assert serialized["details"]["step"] == 1000
        assert serialized["details"]["reason"] == "convergence_failure"
    
    def test_decorator_with_custom_exceptions(self):
        """カスタム例外でのデコレータテスト"""
        @wrap_exception
        def risky_simulation():
            # この関数はシミュレーションエラーを発生させる
            raise SimulationError("計算に失敗しました")
        
        # SimulationError は AstroSimException なので、そのまま通る
        with pytest.raises(SimulationError):
            risky_simulation()
    
    def test_error_level_consistency(self):
        """エラーレベルの一貫性テスト"""
        # 階層構造とエラーレベルの一貫性を確認
        critical_exceptions = [DependencyError("test"), SystemError("test"), GPUError("test")]
        for exc in critical_exceptions:
            assert get_error_level(exc) == ErrorLevel.CRITICAL
        
        # サブクラスも同じレベルになることを確認
        vram_error = VRAMError("VRAM不足")  # GPUError のサブクラス
        assert get_error_level(vram_error) == ErrorLevel.CRITICAL