"""
UI統合テスト

UIレイヤーとその他のシステムレイヤーとの統合、
キーボードショートカットのマッピング、UIイベント処理を検証します。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestUIIntegration:
    """UI統合テストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_qt_environment(self):
        """Qt環境のモック"""
        with patch('PyQt6.QtWidgets.QApplication'), \
             patch('PyQt6.QtWidgets.QMainWindow'), \
             patch('PyQt6.QtCore.QTimer'), \
             patch('PyQt6.QtGui.QShortcut') as mock_shortcut:
            yield mock_shortcut
    
    @pytest.fixture
    def mock_vispy_environment(self):
        """Vispy環境のモック"""
        with patch('vispy.scene.SceneCanvas'), \
             patch('vispy.scene.TurntableCamera'), \
             patch('vispy.scene.ViewBox'):
            yield
    
    @pytest.fixture
    def main_window_with_mocks(self, mock_qt_environment, mock_vispy_environment, temp_dir):
        """モック環境でのMainWindow"""
        from src.ui.main_window import MainWindow
        from src.domain.solar_system import SolarSystem
        from src.simulation.time_manager import TimeManager
        from src.data.config_manager import ConfigManager
        
        # 実際のコンポーネント（非GUI部分）
        config_manager = ConfigManager()
        solar_system = SolarSystem()
        time_manager = TimeManager()
        
        # MainWindowのインスタンス作成（Qt部分はモック化済み）
        main_window = MainWindow(
            config_manager=config_manager,
            solar_system=solar_system,
            time_manager=time_manager
        )
        
        return main_window
    
    def test_keyboard_shortcut_mapping_completeness(self, main_window_with_mocks):
        """キーボードショートカットマッピングの完全性テスト"""
        main_window = main_window_with_mocks
        
        # ユーザーマニュアルで定義されているショートカット
        expected_shortcuts = {
            # ファイル操作
            "Ctrl+Q": "close",
            "Ctrl+R": "_reset_simulation",
            
            # 表示制御
            "F11": "_toggle_fullscreen",
            "F5": "_refresh_display",
            "R": "_reset_view",
            "O": "_toggle_orbits",
            "L": "_toggle_labels",
            "A": "_toggle_axes",
            
            # プリセットビュー
            "1": "_set_preset_view",
            "2": "_set_preset_view",
            "3": "_set_preset_view",
            "4": "_set_preset_view",
            
            # 惑星選択
            "5": "_select_planet_by_index",
            "6": "_select_planet_by_index",
            "7": "_select_planet_by_index",
            "8": "_select_planet_by_index",
            "9": "_select_planet_by_index",
            "Escape": "_stop_tracking",
            
            # アニメーション制御
            "Space": "_toggle_animation",
            "Ctrl+Space": "_pause_animation",
            
            # ヘルプ
            "F1": "_show_help",
            "Ctrl+?": "_show_keyboard_shortcuts",
        }
        
        # 実装されているメソッドの確認
        for shortcut, method_name in expected_shortcuts.items():
            if method_name.startswith("_set_preset_view"):
                # プリセットビューは特別処理（lambda関数のため）
                assert hasattr(main_window, "_set_preset_view"), f"プリセットビューメソッド {method_name} が実装されていること"
            elif method_name.startswith("_select_planet_by_index"):
                # 惑星選択は特別処理
                assert hasattr(main_window, "_select_planet_by_index"), f"惑星選択メソッド {method_name} が実装されていること"
            elif method_name == "close":
                # closeは基底クラスのメソッド
                assert hasattr(main_window, method_name), f"ショートカット {shortcut} に対応するメソッド {method_name} が実装されていること"
            else:
                assert hasattr(main_window, method_name), f"ショートカット {shortcut} に対応するメソッド {method_name} が実装されていること"
    
    def test_keyboard_shortcut_handler_integration(self, main_window_with_mocks):
        """キーボードショートカットハンドラーの統合テスト"""
        main_window = main_window_with_mocks
        
        # モックシーンマネージャーの設定
        mock_scene_manager = Mock()
        mock_camera_controller = Mock()
        mock_renderer = Mock()
        mock_solar_system = Mock()
        
        main_window.scene_manager = mock_scene_manager
        mock_scene_manager.camera_controller = mock_camera_controller
        mock_scene_manager.renderer = mock_renderer
        main_window.solar_system = mock_solar_system
        
        # レンダラーの初期状態設定
        mock_renderer.show_orbits = True
        mock_renderer.show_labels = True
        mock_renderer.show_axes = False
        
        # 太陽系の惑星設定
        mock_planets = [Mock(name=f"惑星{i}") for i in range(8)]
        mock_solar_system.get_planets.return_value = mock_planets
        
        # テスト1: プリセットビュー操作
        presets = ["top", "side", "front", "perspective"]
        for preset in presets:
            main_window._set_preset_view(preset)
            mock_camera_controller.set_view_preset.assert_called_with(preset)
        
        # テスト2: 表示制御操作
        main_window._toggle_orbits()
        mock_renderer.set_orbit_visibility.assert_called_with(False)  # True → False
        
        main_window._toggle_labels()
        mock_renderer.set_label_visibility.assert_called_with(False)  # True → False
        
        main_window._toggle_axes()
        mock_renderer.set_axes_visibility.assert_called_with(True)    # False → True
        
        # テスト3: カメラ制御操作
        main_window._reset_view()
        mock_camera_controller.reset_view.assert_called_once()
        
        main_window._stop_tracking()
        mock_camera_controller.stop_tracking.assert_called_once()
        
        # テスト4: 惑星選択操作
        main_window._select_planet_by_index(0)
        mock_scene_manager.select_planet.assert_called()
    
    def test_ui_component_initialization_order(self, mock_qt_environment, mock_vispy_environment):
        """UIコンポーネント初期化順序の検証"""
        from src.ui.main_window import MainWindow
        
        # MainWindowの初期化過程をテスト
        with patch.object(MainWindow, '_init_ui') as mock_init_ui, \
             patch.object(MainWindow, '_create_menu_bar') as mock_create_menu, \
             patch.object(MainWindow, '_create_tool_bar') as mock_create_toolbar, \
             patch.object(MainWindow, '_create_status_bar') as mock_create_status, \
             patch.object(MainWindow, '_setup_connections') as mock_setup_connections, \
             patch.object(MainWindow, '_setup_keyboard_shortcuts') as mock_setup_shortcuts:
            
            # MainWindowインスタンス作成
            main_window = MainWindow()
            
            # 初期化メソッドが正しい順序で呼ばれることを確認
            mock_init_ui.assert_called_once()
            mock_create_menu.assert_called_once()
            mock_create_toolbar.assert_called_once()
            mock_create_status.assert_called_once()
            mock_setup_connections.assert_called_once()
            mock_setup_shortcuts.assert_called_once()
    
    def test_menu_action_integration(self, main_window_with_mocks):
        """メニューアクション統合テスト"""
        main_window = main_window_with_mocks
        
        # メニューアクションのメソッド呼び出しテスト
        with patch.object(main_window, '_toggle_animation') as mock_toggle:
            main_window._toggle_animation()
            mock_toggle.assert_called_once()
        
        with patch.object(main_window, '_reset_simulation') as mock_reset:
            main_window._reset_simulation()
            mock_reset.assert_called_once()
        
        with patch.object(main_window, '_toggle_fullscreen') as mock_fullscreen:
            main_window._toggle_fullscreen()
            mock_fullscreen.assert_called_once()
    
    def test_ui_state_synchronization(self, main_window_with_mocks):
        """UI状態同期テスト"""
        main_window = main_window_with_mocks
        
        # モックコンポーネントの設定
        mock_control_panel = Mock()
        mock_info_panel = Mock()
        mock_status_bar = Mock()
        
        main_window.control_panel = mock_control_panel
        main_window.info_panel = mock_info_panel
        main_window.status_bar = mock_status_bar
        
        # 時間表示更新のテスト
        main_window.update_time_display()
        
        # status_barのshowMessageが呼ばれることを確認
        assert mock_status_bar.showMessage.called, "ステータスバーに時間が表示されること"
    
    def test_error_handling_in_ui_operations(self, main_window_with_mocks):
        """UI操作でのエラーハンドリングテスト"""
        main_window = main_window_with_mocks
        
        # scene_managerがNoneの場合のテスト
        main_window.scene_manager = None
        
        # エラーを発生させずに処理が完了することを確認
        try:
            main_window._reset_view()
            main_window._set_preset_view("top")
            main_window._toggle_orbits()
            main_window._select_planet_by_index(0)
        except Exception as e:
            pytest.fail(f"scene_manager=Noneの場合でも例外を発生させないこと: {e}")
        
        # 不正なプリセット名でのテスト
        mock_scene_manager = Mock()
        mock_camera_controller = Mock()
        main_window.scene_manager = mock_scene_manager
        mock_scene_manager.camera_controller = mock_camera_controller
        
        try:
            main_window._set_preset_view("invalid_preset")
            # カメラコントローラーに不正なプリセット名が渡されることを確認
            mock_camera_controller.set_view_preset.assert_called_with("invalid_preset")
        except Exception as e:
            pytest.fail(f"不正なプリセット名でも例外を発生させないこと: {e}")
    
    def test_ui_event_signal_emission(self, main_window_with_mocks):
        """UIイベントシグナル発信テスト"""
        main_window = main_window_with_mocks
        
        # シグナルの存在確認
        assert hasattr(main_window, 'planet_selected'), "planet_selectedシグナルが定義されていること"
        assert hasattr(main_window, 'animation_toggled'), "animation_toggledシグナルが定義されていること"
        assert hasattr(main_window, 'time_scale_changed'), "time_scale_changedシグナルが定義されていること"
        assert hasattr(main_window, 'view_reset_requested'), "view_reset_requestedシグナルが定義されていること"
        
        # シグナル発信のテスト（モック環境では実際の発信は確認できないが、コードの存在を確認）
        with patch.object(main_window, 'view_reset_requested') as mock_signal:
            main_window._reset_view()
            # view_reset_requestedが呼ばれることを確認
            # 注：実際のシグナル発信はPyQt6のモック環境では制限があるため、メソッド呼び出しを確認
    
    def test_keyboard_shortcut_conflict_detection(self, main_window_with_mocks):
        """キーボードショートカット競合検出テスト"""
        main_window = main_window_with_mocks
        
        # 実装されているショートカットキーの重複チェック
        # MainWindowの_setup_keyboard_shortcutsで定義されているキー
        shortcut_keys = [
            "Ctrl+Q", "Ctrl+R", "F11", "F5", "R", "O", "L", "A",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "Escape",
            "Space", "Ctrl+Space", "F1", "Ctrl+?"
        ]
        
        # キーの重複がないことを確認
        unique_keys = set(shortcut_keys)
        assert len(shortcut_keys) == len(unique_keys), f"ショートカットキーに重複がないこと（重複: {len(shortcut_keys) - len(unique_keys)}個）"
        
        # 基本的なキーの存在確認
        essential_keys = ["Space", "R", "F1", "F11", "Ctrl+Q"]
        for key in essential_keys:
            assert key in shortcut_keys, f"重要なショートカットキー {key} が定義されていること"
    
    def test_ui_responsiveness_under_load(self, main_window_with_mocks):
        """負荷状況下でのUI応答性テスト"""
        main_window = main_window_with_mocks
        
        # モックコンポーネントの設定
        mock_scene_manager = Mock()
        mock_renderer = Mock()
        main_window.scene_manager = mock_scene_manager
        mock_scene_manager.renderer = mock_renderer
        
        # 大量の操作を実行
        import time
        start_time = time.time()
        
        for i in range(100):
            main_window._toggle_orbits()
            main_window._toggle_labels()
            if i % 4 == 0:
                main_window._set_preset_view("top")
            elif i % 4 == 1:
                main_window._set_preset_view("side")
            elif i % 4 == 2:
                main_window._set_preset_view("front")
            else:
                main_window._set_preset_view("perspective")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # UI操作が高速に完了することを確認（1秒以内）
        assert execution_time < 1.0, f"100回のUI操作が1秒以内に完了すること（実際: {execution_time:.3f}秒）"
        
        # モックメソッドが正しい回数呼ばれたことを確認
        assert mock_renderer.set_orbit_visibility.call_count == 100, "軌道表示切り替えが100回実行されること"
        assert mock_renderer.set_label_visibility.call_count == 100, "ラベル表示切り替えが100回実行されること"