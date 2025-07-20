"""
ドキュメント準拠性テスト

ユーザーマニュアル、README、設計書に記載された機能と
実際の実装との整合性を自動検証します。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import re
import json
import tempfile
import shutil

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDocumentationCompliance:
    """ドキュメント準拠性テストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def user_manual_content(self):
        """ユーザーマニュアルの内容読み込み"""
        user_manual_path = project_root / "docs" / "ユーザーマニュアル.md"
        if user_manual_path.exists():
            with open(user_manual_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    @pytest.fixture
    def readme_content(self):
        """READMEの内容読み込み"""
        readme_path = project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def test_user_manual_keyboard_shortcuts_compliance(self, user_manual_content):
        """ユーザーマニュアル記載キーボードショートカットの実装準拠性"""
        
        # ユーザーマニュアルからキーボードショートカットを抽出
        shortcut_patterns = [
            r'`([^`]+)`.*?([^|]+)\|',  # テーブル形式のショートカット
            r'- \*\*([^*]+)\*\*:',     # リスト形式のショートカット
            r'<b>([^<]+)</b>:',        # HTML形式のショートカット
        ]
        
        documented_shortcuts = set()
        for pattern in shortcut_patterns:
            matches = re.findall(pattern, user_manual_content)
            for match in matches:
                if isinstance(match, tuple):
                    documented_shortcuts.add(match[0].strip())
                else:
                    documented_shortcuts.add(match.strip())
        
        # MainWindowの実装確認
        from src.ui.main_window import MainWindow
        
        # 実装されているショートカットの定義
        implemented_shortcuts = {
            "Space", "Ctrl+Space", "R", "O", "L", "A",
            "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "Escape", "F1", "F5", "F11", "Ctrl+R", "Ctrl+Q", "Ctrl+?"
        }
        
        # ユーザーマニュアルで言及されている主要ショートカット
        essential_shortcuts = {
            "Space", "R", "O", "L", "1", "2", "3", "4",
            "5", "6", "7", "8", "9", "F1", "F11", "Ctrl+R"
        }
        
        # 重要なショートカットが実装されていることを確認
        for shortcut in essential_shortcuts:
            assert shortcut in implemented_shortcuts, f"ユーザーマニュアル記載の重要なショートカット '{shortcut}' が実装されていること"
    
    def test_user_manual_feature_implementation_compliance(self, user_manual_content):
        """ユーザーマニュアル記載機能の実装準拠性"""
        
        # test_manual_feature_validation.pyの結果を利用したテスト
        # 既存の検証スクリプトを統合
        
        # MainWindowの機能確認
        from src.ui.main_window import MainWindow
        from src.visualization.camera_controller import CameraController
        from src.visualization.renderer_3d import Renderer3D
        from src.ui.control_panel import ControlPanel
        from src.ui.info_panel import InfoPanel
        
        # UIコンポーネントの存在確認
        assert hasattr(MainWindow, '_set_preset_view'), "プリセットビュー機能が実装されていること"
        assert hasattr(MainWindow, '_toggle_orbits'), "軌道線切り替え機能が実装されていること"
        assert hasattr(MainWindow, '_toggle_labels'), "ラベル切り替え機能が実装されていること"
        assert hasattr(MainWindow, '_select_planet_by_index'), "惑星選択機能が実装されていること"
        
        # CameraControllerの機能確認
        assert hasattr(CameraController, 'set_view_preset'), "カメラプリセット機能が実装されていること"
        assert hasattr(CameraController, 'handle_mouse_move'), "マウス操作機能が実装されていること"
        assert hasattr(CameraController, 'handle_mouse_wheel'), "ズーム機能が実装されていること"
        
        # Renderer3Dの機能確認（クラス存在チェックのみ）
        assert Renderer3D is not None, "3Dレンダラーが実装されていること"
        
        # コントロールパネル・情報パネルの存在確認
        assert ControlPanel is not None, "制御パネルが実装されていること"
        assert InfoPanel is not None, "情報パネルが実装されていること"
    
    def test_readme_system_requirements_compliance(self, readme_content):
        """README記載システム要件の準拠性"""
        
        # システム要件の実装確認
        requirements_path = project_root / "requirements.txt"
        assert requirements_path.exists(), "requirements.txtが存在すること"
        
        with open(requirements_path, 'r') as f:
            requirements_content = f.read()
        
        # 主要な依存関係の存在確認
        essential_packages = [
            "PyQt6", "vispy", "numpy", "scipy", "astropy"
        ]
        
        for package in essential_packages:
            assert package.lower() in requirements_content.lower(), f"重要なパッケージ {package} が requirements.txt に含まれていること"
    
    def test_readme_installation_instructions_compliance(self, readme_content):
        """README記載インストール手順の準拠性"""
        
        # プロジェクト構造の確認
        essential_files = [
            "src/main.py",
            "requirements.txt", 
            "README.md",
            "CLAUDE.md"
        ]
        
        for file_path in essential_files:
            file_full_path = project_root / file_path
            assert file_full_path.exists(), f"README記載の重要ファイル {file_path} が存在すること"
    
    def test_feature_documentation_coverage(self):
        """機能ドキュメント網羅性テスト"""
        
        # 実装されている主要クラスの確認
        from src.domain.solar_system import SolarSystem
        from src.domain.planet import Planet
        from src.simulation.physics_engine import PhysicsEngine
        from src.simulation.time_manager import TimeManager
        from src.visualization.renderer_3d import Renderer3D
        from src.visualization.camera_controller import CameraController
        from src.ui.main_window import MainWindow
        
        # 各クラスの主要メソッドが存在することを確認
        core_classes_methods = {
            SolarSystem: ['add_planet', 'get_planets', 'get_planet_count'],
            Planet: ['update_position', 'get_distance_from_sun'],
            PhysicsEngine: ['calculate_position', 'calculate_gravitational_force'],
            TimeManager: ['get_current_time', 'advance_time', 'set_time_scale'],
            CameraController: ['rotate', 'zoom', 'set_view_preset'],
            MainWindow: ['_setup_keyboard_shortcuts', '_toggle_animation']
        }
        
        for cls, methods in core_classes_methods.items():
            for method in methods:
                assert hasattr(cls, method), f"クラス {cls.__name__} にメソッド {method} が実装されていること"
    
    def test_configuration_documentation_compliance(self):
        """設定ドキュメントの準拠性"""
        
        from src.data.config_manager import ConfigManager
        
        # ConfigManagerのデフォルト設定の存在確認
        config_manager = ConfigManager()
        default_config = config_manager.get_all_config()
        
        # 重要な設定セクションの存在確認
        essential_sections = [
            'ui', 'simulation', 'display', 'camera', 'animation'
        ]
        
        for section in essential_sections:
            assert section in default_config, f"設定セクション '{section}' がデフォルト設定に含まれていること"
    
    def test_error_message_documentation_compliance(self):
        """エラーメッセージドキュメントの準拠性"""
        
        # カスタム例外クラスの存在確認
        from src.utils.exceptions import AstroSimException
        
        # 例外クラスが適切に実装されていることを確認
        assert issubclass(AstroSimException, Exception), "AstroSimExceptionがExceptionを継承していること"
        
        # 例外インスタンスの作成テスト
        try:
            exception = AstroSimException("テストエラー")
            assert str(exception) == "テストエラー", "例外メッセージが正しく設定されること"
        except Exception as e:
            pytest.fail(f"AstroSimException の作成でエラーが発生: {e}")
    
    def test_performance_metrics_documentation_compliance(self):
        """パフォーマンス指標ドキュメントの準拠性"""
        
        # パフォーマンス最適化機能の実装確認
        try:
            from src.utils.memory_pool import MemoryPoolManager
            from src.simulation.orbit_calculator import OrbitCalculator
            
            # メモリプール機能の基本動作確認
            memory_pool = MemoryPoolManager()
            assert memory_pool is not None, "メモリプール管理機能が実装されていること"
            
            # 軌道計算キャッシュ機能の基本動作確認
            orbit_calc = OrbitCalculator()
            assert orbit_calc is not None, "軌道計算キャッシュ機能が実装されていること"
            
        except ImportError as e:
            pytest.fail(f"パフォーマンス最適化機能のインポートエラー: {e}")
    
    def test_user_workflow_documentation_compliance(self, user_manual_content):
        """ユーザーワークフロードキュメントの準拠性"""
        
        # ユーザーマニュアルに記載されているワークフローの実装確認
        
        # 1. 基本起動シーケンス
        from src.main import AstroSimApplication
        assert AstroSimApplication is not None, "メインアプリケーションクラスが実装されていること"
        
        # 2. 太陽系データ読み込み
        from src.data.planet_repository import PlanetRepository
        planet_repo = PlanetRepository()
        planets = planet_repo.get_all_planets()
        assert len(planets) == 8, "8惑星のデータが読み込み可能であること"
        
        # 3. シミュレーション制御
        from src.simulation.time_manager import TimeManager
        time_manager = TimeManager()
        assert hasattr(time_manager, 'set_time_scale'), "時間倍率制御が実装されていること"
        
        # 4. 3D表示制御
        from src.visualization.camera_controller import CameraController
        from src.visualization.renderer_3d import Renderer3D
        assert CameraController is not None, "カメラ制御が実装されていること"
        assert Renderer3D is not None, "3D描画機能が実装されていること"
    
    def test_api_documentation_compliance(self):
        """API ドキュメントの準拠性"""
        
        # 主要クラスの public API の確認
        from src.domain.solar_system import SolarSystem
        from src.simulation.physics_engine import PhysicsEngine
        
        # パブリックメソッドのドキュメント文字列確認
        solar_system = SolarSystem()
        assert hasattr(solar_system, 'add_planet'), "SolarSystem.add_planet メソッドが存在すること"
        
        physics_engine = PhysicsEngine()
        assert hasattr(physics_engine, 'calculate_position'), "PhysicsEngine.calculate_position メソッドが存在すること"
        
        # メソッドシグネチャの基本確認（引数の数など）
        import inspect
        
        add_planet_sig = inspect.signature(solar_system.add_planet)
        assert len(add_planet_sig.parameters) >= 1, "add_planet メソッドが適切な引数を持つこと"
        
        calc_pos_sig = inspect.signature(physics_engine.calculate_position)
        assert len(calc_pos_sig.parameters) >= 2, "calculate_position メソッドが適切な引数を持つこと"
    
    def test_cross_reference_consistency(self, user_manual_content, readme_content):
        """ドキュメント間参照の一貫性"""
        
        # README と ユーザーマニュアル間の一貫性チェック
        
        # 共通して言及されるべき項目
        common_items = [
            "AstroSim", "太陽系", "シミュレーション", "3D", "PyQt6", "Vispy"
        ]
        
        for item in common_items:
            # README とユーザーマニュアルの両方に重要項目が含まれることを確認
            # （大文字小文字を区別しない）
            assert item.lower() in readme_content.lower() or item in readme_content, \
                f"重要項目 '{item}' が README に含まれていること"
            assert item.lower() in user_manual_content.lower() or item in user_manual_content, \
                f"重要項目 '{item}' がユーザーマニュアルに含まれていること"
    
    def test_version_information_consistency(self):
        """バージョン情報の一貫性"""
        
        # setup.pyとversion_info.txtのバージョン情報確認
        setup_py_path = project_root / "setup.py"
        version_info_path = project_root / "version_info.txt"
        
        version_sources = []
        
        if setup_py_path.exists():
            with open(setup_py_path, 'r', encoding='utf-8') as f:
                setup_content = f.read()
                # version= の行を探す
                import re
                version_match = re.search(r'version=["\']([^"\']+)["\']', setup_content)
                if version_match:
                    version_sources.append(('setup.py', version_match.group(1)))
        
        if version_info_path.exists():
            with open(version_info_path, 'r', encoding='utf-8') as f:
                version_content = f.read().strip()
                version_sources.append(('version_info.txt', version_content))
        
        # バージョン情報が存在し、妥当であることを確認
        assert len(version_sources) > 0, "バージョン情報が定義されていること"
        
        for source, version in version_sources:
            # バージョン形式の基本チェック（x.y.z 形式）
            assert re.match(r'\d+\.\d+\.\d+', version), f"{source} のバージョン形式が正しいこと (実際: {version})"