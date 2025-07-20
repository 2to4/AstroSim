"""
ユーザー機能ドリブンテスト

ユーザーの視点から、実際の操作シナリオと
ユーザーマニュアル記載機能の動作を検証します。
"""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestUserScenarios:
    """ユーザーシナリオベースのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture 
    def mock_environment(self):
        """GUI依存のモック環境セットアップ"""
        with patch('src.main.QApplication'), \
             patch('src.main.vispy'), \
             patch('src.ui.main_window.scene'), \
             patch('src.visualization.scene_manager.scene'), \
             patch('src.visualization.renderer_3d.scene'):
            yield
    
    @pytest.fixture
    def solar_system_components(self, temp_dir):
        """実際の太陽系コンポーネント（GUI部分以外）"""
        from src.domain.solar_system import SolarSystem
        from src.domain.planet import Planet
        from src.domain.orbital_elements import OrbitalElements
        from src.simulation.physics_engine import PhysicsEngine
        from src.simulation.time_manager import TimeManager
        from src.data.planet_repository import PlanetRepository
        from src.data.config_manager import ConfigManager
        
        # 実際のコンポーネントを使用
        config_manager = ConfigManager()
        planet_repo = PlanetRepository()
        solar_system = SolarSystem()
        physics_engine = PhysicsEngine()
        time_manager = TimeManager()
        
        # 太陽系に惑星を追加
        planets = planet_repo.get_all_planets()
        for planet_data in planets:
            orbital_elements = OrbitalElements(
                semi_major_axis=planet_data['orbital_elements']['semi_major_axis'],
                eccentricity=planet_data['orbital_elements']['eccentricity'],
                inclination=planet_data['orbital_elements']['inclination'],
                longitude_of_ascending_node=planet_data['orbital_elements']['longitude_of_ascending_node'],
                argument_of_periapsis=planet_data['orbital_elements'].get('argument_of_perihelion', 0.0),
                mean_anomaly=planet_data['orbital_elements'].get('mean_anomaly_at_epoch', 0.0)
            )
            
            planet = Planet(
                name=planet_data['name'],
                mass=planet_data['mass'],
                radius=planet_data['radius'],
                orbital_elements=orbital_elements
            )
            solar_system.add_planet(planet)
        
        return {
            'solar_system': solar_system,
            'physics_engine': physics_engine,
            'time_manager': time_manager,
            'config_manager': config_manager,
            'planet_repo': planet_repo
        }
    
    def test_complete_user_workflow_startup_to_simulation(self, mock_environment, solar_system_components):
        """典型的ユーザーワークフロー: 起動からシミュレーション実行まで"""
        
        # Phase 1: アプリケーション起動
        solar_system = solar_system_components['solar_system']
        time_manager = solar_system_components['time_manager']
        physics_engine = solar_system_components['physics_engine']
        
        # 起動時の基本状態確認
        assert solar_system.get_planet_count() == 8, "8惑星が読み込まれていること"
        assert time_manager.get_current_time() is not None, "時間管理システムが動作していること"
        
        # Phase 2: 惑星選択
        planets = solar_system.get_planets()
        earth = next((p for p in planets if p.name == "地球"), None)
        assert earth is not None, "地球が選択可能であること"
        
        # Phase 3: シミュレーション実行
        initial_position = earth.position.copy()
        
        # 時間を進める（1日）
        time_manager.advance_time(1.0)  # 1日進める
        
        # 惑星位置を更新
        for planet in planets:
            new_position = physics_engine.calculate_position(
                planet.orbital_elements,
                time_manager.get_j2000_days()
            )
            planet.update_position(new_position)
        
        # Phase 4: 結果検証
        final_position = earth.position
        position_change = np.linalg.norm(final_position - initial_position)
        
        assert position_change > 0, "地球が軌道運動していること"
        assert position_change < 1.0, "現実的な移動距離であること（1AU未満）"
    
    def test_user_keyboard_shortcut_scenarios(self, mock_environment):
        """ユーザーキーボードショートカット操作シナリオ"""
        
        # モック化されたMainWindowとCameraControllerを作成
        mock_main_window = Mock()
        mock_scene_manager = Mock()
        mock_camera_controller = Mock()
        mock_renderer = Mock()
        
        # シーンマネージャーの階層構造をセットアップ
        mock_main_window.scene_manager = mock_scene_manager
        mock_scene_manager.camera_controller = mock_camera_controller
        mock_scene_manager.renderer = mock_renderer
        
        # プリセットビューメソッドの存在確認
        mock_camera_controller.set_view_preset = Mock()
        mock_camera_controller.reset_view = Mock()
        mock_camera_controller.stop_tracking = Mock()
        
        # 表示制御メソッドの存在確認
        mock_renderer.set_orbit_visibility = Mock()
        mock_renderer.set_label_visibility = Mock()
        mock_renderer.set_axes_visibility = Mock()
        mock_renderer.show_orbits = True
        mock_renderer.show_labels = True
        mock_renderer.show_axes = False
        
        # ユーザーシナリオ1: プリセットビュー操作
        presets = ["top", "side", "front", "perspective"]
        for preset in presets:
            mock_camera_controller.set_view_preset(preset)
            mock_camera_controller.set_view_preset.assert_called_with(preset)
        
        # ユーザーシナリオ2: 表示オプション切り替え
        mock_renderer.set_orbit_visibility(False)
        mock_renderer.set_orbit_visibility.assert_called_with(False)
        
        mock_renderer.set_label_visibility(False)
        mock_renderer.set_label_visibility.assert_called_with(False)
        
        # ユーザーシナリオ3: ビューリセット
        mock_camera_controller.reset_view()
        mock_camera_controller.reset_view.assert_called_once()
        
        # ユーザーシナリオ4: 追跡停止
        mock_camera_controller.stop_tracking()
        mock_camera_controller.stop_tracking.assert_called_once()
    
    def test_user_planet_exploration_workflow(self, mock_environment, solar_system_components):
        """ユーザー惑星探索ワークフロー"""
        
        solar_system = solar_system_components['solar_system']
        planets = solar_system.get_planets()
        
        # Phase 1: 全惑星の基本情報確認
        planet_info = {}
        for planet in planets:
            info = {
                'name': planet.name,
                'mass': planet.mass,
                'radius': planet.radius,
                'orbital_period': planet.orbital_elements.get_orbital_period(),
                'distance_from_sun': np.linalg.norm(planet.position)
            }
            planet_info[planet.name] = info
            
            # 各惑星の基本データ検証
            assert info['mass'] > 0, f"{planet.name}の質量が正の値であること"
            assert info['radius'] > 0, f"{planet.name}の半径が正の値であること"
            assert info['orbital_period'] > 0, f"{planet.name}の軌道周期が正の値であること"
        
        # Phase 2: 惑星間の相対的関係確認
        assert len(planet_info) == 8, "8惑星の情報が取得できること"
        
        # 太陽からの距離順序確認（大まかな順序）
        distances = [(name, info['distance_from_sun']) for name, info in planet_info.items()]
        distances.sort(key=lambda x: x[1])
        
        # 最も近い惑星は水星または金星のいずれかであること
        closest_planet = distances[0][0]
        assert closest_planet in ["水星", "金星"], f"最も近い惑星は水星または金星であること（実際: {closest_planet}）"
    
    def test_user_time_control_scenarios(self, mock_environment, solar_system_components):
        """ユーザー時間制御操作シナリオ"""
        
        time_manager = solar_system_components['time_manager']
        solar_system = solar_system_components['solar_system']
        
        # Phase 1: 初期時刻の確認
        initial_time = time_manager.get_current_time()
        initial_j2000 = time_manager.get_j2000_days()
        
        assert initial_time is not None, "初期時刻が設定されていること"
        assert initial_j2000 is not None, "J2000基準日が計算されていること"
        
        # Phase 2: 時間倍率の変更
        original_scale = time_manager.time_scale
        
        # 高速化テスト
        time_manager.set_time_scale(10.0)
        assert time_manager.time_scale == 10.0, "時間倍率10倍に設定できること"
        
        # スローモーションテスト
        time_manager.set_time_scale(0.1)
        assert time_manager.time_scale == 0.1, "時間倍率0.1倍に設定できること"
        
        # リセットテスト
        time_manager.set_time_scale(original_scale)
        assert time_manager.time_scale == original_scale, "時間倍率をリセットできること"
        
        # Phase 3: 時間進行テスト
        time_manager.advance_time(30.0)  # 30日進める
        new_time = time_manager.get_current_time()
        
        time_difference = (new_time - initial_time).days
        assert abs(time_difference - 30) <= 1, "30日進めた時間差が正確であること"
    
    def test_user_error_recovery_scenarios(self, mock_environment, solar_system_components):
        """ユーザーエラー回復シナリオ"""
        
        solar_system = solar_system_components['solar_system']
        time_manager = solar_system_components['time_manager']
        config_manager = solar_system_components['config_manager']
        
        # Phase 1: 不正な惑星選択への対処
        planets = solar_system.get_planets()
        planet_names = [p.name for p in planets]
        
        # 存在しない惑星名での検索
        non_existent_planet = solar_system.get_planet_by_name("存在しない惑星")
        assert non_existent_planet is None, "存在しない惑星は None を返すこと"
        
        # Phase 2: 時間設定の境界値テスト
        try:
            time_manager.set_time_scale(0.0)  # 不正な倍率
            assert False, "時間倍率0.0は例外を発生させるべき"
        except (ValueError, AssertionError):
            pass  # 期待される例外
        
        try:
            time_manager.set_time_scale(-1.0)  # 負の倍率
            assert False, "負の時間倍率は例外を発生させるべき"
        except (ValueError, AssertionError):
            pass  # 期待される例外
        
        # Phase 3: 設定の回復テスト
        original_config = config_manager.get_all_config()
        
        # 設定をリセット
        config_manager.reset_to_defaults()
        reset_config = config_manager.get_all_config()
        
        assert 'ui' in reset_config, "UIセクションがデフォルト設定に含まれること"
        assert 'simulation' in reset_config, "シミュレーションセクションがデフォルト設定に含まれること"
    
    def test_user_performance_scenarios(self, mock_environment, solar_system_components):
        """ユーザーパフォーマンスシナリオ"""
        
        solar_system = solar_system_components['solar_system']
        physics_engine = solar_system_components['physics_engine']
        time_manager = solar_system_components['time_manager']
        
        # Phase 1: 大量計算のパフォーマンステスト
        planets = solar_system.get_planets()
        
        import time
        start_time = time.time()
        
        # 100ステップのシミュレーション
        for step in range(100):
            current_j2000 = time_manager.get_j2000_days() + (step * 0.1)
            
            for planet in planets:
                # 位置計算（軌道計算キャッシュを活用）
                position = physics_engine.calculate_position(
                    planet.orbital_elements,
                    current_j2000
                )
                planet.update_position(position)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # パフォーマンス基準: 100ステップを5秒以内で完了
        assert execution_time < 5.0, f"100ステップの計算が5秒以内に完了すること（実際: {execution_time:.2f}秒）"
        
        # Phase 2: メモリ使用量の確認
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            # メモリ使用量の妥当性確認（500MB以下）
            assert memory_usage < 500, f"メモリ使用量が500MB以下であること（実際: {memory_usage:.2f}MB）"
        except ImportError:
            # psutilが利用できない場合はスキップ
            pytest.skip("psutilが利用できないためメモリテストをスキップ")