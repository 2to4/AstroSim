"""
ConfigManagerクラスの単体テスト

設定管理の全機能を検証します。
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from src.data.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerクラスのテスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        # 一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "test_config.json"
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_with_default_path(self):
        """デフォルトパスでの初期化テスト"""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            
            config = ConfigManager()
            
            expected_path = self.temp_dir / ".astrosim" / "config.json"
            assert config.config_path == expected_path
            assert expected_path.parent.exists()
    
    def test_initialization_with_custom_path(self):
        """カスタムパスでの初期化テスト"""
        config = ConfigManager(self.config_path)
        
        assert config.config_path == self.config_path
        assert isinstance(config._config, dict)
        assert isinstance(config._default_config, dict)
    
    def test_default_config_structure(self):
        """デフォルト設定の構造テスト"""
        config = ConfigManager(self.config_path)
        
        # 必須セクションの存在確認
        required_sections = [
            'application', 'window', 'simulation', 'display',
            'camera', 'data', 'performance', 'ui', 'shortcuts', 'logging'
        ]
        
        for section in required_sections:
            assert section in config._default_config
            assert isinstance(config._default_config[section], dict)
        
        # 具体的な設定値の確認
        assert config._default_config['application']['version'] == "1.0.0"
        assert config._default_config['window']['width'] == 1600
        assert config._default_config['simulation']['fps'] == 60
        assert config._default_config['display']['show_orbits'] is True
    
    def test_create_default_config_file(self):
        """デフォルト設定ファイル作成のテスト"""
        # 設定ファイルが存在しない状態で初期化
        config = ConfigManager(self.config_path)
        
        # ファイルが作成されることを確認
        assert self.config_path.exists()
        
        # ファイル内容の確認
        with open(self.config_path, 'r', encoding='utf-8') as file:
            saved_config = json.load(file)
        
        assert '_metadata' in saved_config
        assert 'application' in saved_config
        assert saved_config['application']['version'] == "1.0.0"
    
    def test_load_existing_config(self):
        """既存設定ファイルの読み込みテスト"""
        # テスト用設定ファイルを作成
        test_config = {
            "application": {
                "version": "2.0.0",
                "language": "en"
            },
            "window": {
                "width": 1920,
                "height": 1080
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as file:
            json.dump(test_config, file)
        
        # 設定を読み込み
        config = ConfigManager(self.config_path)
        
        # ユーザー設定が反映されているか確認
        assert config.get('application.version') == "2.0.0"
        assert config.get('application.language') == "en"
        assert config.get('window.width') == 1920
        
        # デフォルト値がマージされているか確認
        assert config.get('application.theme') == "default"  # デフォルト値
        assert config.get('simulation.fps') == 60  # デフォルト値
    
    def test_malformed_config_fallback(self):
        """不正な設定ファイルのフォールバック処理テスト"""
        # 不正なJSONファイルを作成
        with open(self.config_path, 'w') as file:
            file.write("{ invalid json }")
        
        # 設定を読み込み（エラーが発生するがフォールバックされる）
        config = ConfigManager(self.config_path)
        
        # デフォルト設定が使用されることを確認
        assert config.get('application.version') == "1.0.0"
        assert config.get('window.width') == 1600
    
    def test_get_method(self):
        """get メソッドのテスト"""
        config = ConfigManager(self.config_path)
        
        # 通常の取得
        assert config.get('application.version') == "1.0.0"
        assert config.get('window.width') == 1600
        
        # 存在しないキーのデフォルト値
        assert config.get('nonexistent.key') is None
        assert config.get('nonexistent.key', 'default') == 'default'
        
        # ネストした存在しないキー
        assert config.get('application.nonexistent') is None
        assert config.get('nonexistent.nested.key', 42) == 42
    
    def test_set_method(self):
        """set メソッドのテスト"""
        config = ConfigManager(self.config_path)
        
        # 既存キーの更新
        config.set('application.version', '3.0.0')
        assert config.get('application.version') == '3.0.0'
        
        # 新しいキーの作成
        config.set('custom.new_setting', 'test_value')
        assert config.get('custom.new_setting') == 'test_value'
        
        # ネストした新しいキーの作成
        config.set('new_section.nested.deep', 'deep_value')
        assert config.get('new_section.nested.deep') == 'deep_value'
    
    def test_save_and_load_cycle(self):
        """保存・読み込みサイクルのテスト"""
        # 設定を変更
        config1 = ConfigManager(self.config_path)
        config1.set('application.version', '4.0.0')
        config1.set('window.width', 2560)
        config1.set('custom.test', 'value')
        
        # 保存
        assert config1.save() is True
        
        # 新しいインスタンスで読み込み
        config2 = ConfigManager(self.config_path)
        
        # 変更が反映されているか確認
        assert config2.get('application.version') == '4.0.0'
        assert config2.get('window.width') == 2560
        assert config2.get('custom.test') == 'value'
    
    def test_save_with_backup(self):
        """バックアップ付き保存のテスト"""
        # 初期設定ファイルを作成
        config = ConfigManager(self.config_path)
        config.save()
        
        # 設定を変更して再保存
        config.set('test.backup', 'test')
        config.save()
        
        # バックアップファイルの存在確認
        backup_path = self.config_path.with_suffix('.bak')
        assert backup_path.exists()
    
    def test_reset_to_default(self):
        """デフォルトリセットのテスト"""
        config = ConfigManager(self.config_path)
        
        # 設定を変更
        config.set('application.version', '5.0.0')
        config.set('window.width', 3000)
        
        # 特定セクションのリセット
        config.reset_to_default('application')
        assert config.get('application.version') == '1.0.0'  # リセットされた
        assert config.get('window.width') == 3000  # 変更されていない
        
        # 全体のリセット
        config.reset_to_default()
        assert config.get('window.width') == 1600  # リセットされた
    
    def test_validate_config(self):
        """設定検証のテスト"""
        config = ConfigManager(self.config_path)
        
        # 正常な設定での検証
        errors = config.validate_config()
        assert len(errors) == 0
        
        # 不正な数値設定
        config.set('window.width', -100)  # 範囲外
        config.set('simulation.fps', 'invalid')  # 文字列
        
        errors = config.validate_config()
        assert len(errors) >= 2
        assert any('window.width' in error for error in errors)
        assert any('simulation.fps' in error for error in errors)
        
        # 不正な色設定
        config.set('display.background_color', [1.0, 2.0, 0.5])  # 要素数不足・範囲外
        errors = config.validate_config()
        assert any('display.background_color' in error for error in errors)
    
    def test_section_operations(self):
        """セクション操作のテスト"""
        config = ConfigManager(self.config_path)
        
        # セクション取得
        window_section = config.get_section('window')
        assert isinstance(window_section, dict)
        assert 'width' in window_section
        assert 'height' in window_section
        
        # セクション更新
        new_window_config = {
            'width': 1920,
            'height': 1080,
            'maximized': True
        }
        config.set_section('window', new_window_config)
        
        assert config.get('window.width') == 1920
        assert config.get('window.height') == 1080
        assert config.get('window.maximized') is True
        
        # 全セクション名取得
        sections = config.get_all_sections()
        assert 'application' in sections
        assert 'window' in sections
        assert len(sections) >= 10
    
    def test_export_import_config(self):
        """設定エクスポート・インポートのテスト"""
        export_path = self.temp_dir / "exported_config.json"
        
        # 設定を変更
        config1 = ConfigManager(self.config_path)
        config1.set('application.version', '6.0.0')
        config1.set('custom.export_test', 'exported')
        
        # エクスポート
        assert config1.export_config(export_path) is True
        assert export_path.exists()
        
        # エクスポートファイルの内容確認
        with open(export_path, 'r', encoding='utf-8') as file:
            exported_data = json.load(file)
        
        assert '_export_info' in exported_data
        assert exported_data['application']['version'] == '6.0.0'
        assert exported_data['custom']['export_test'] == 'exported'
        
        # 新しい設定で初期化
        config2 = ConfigManager(self.temp_dir / "import_test.json")
        
        # インポート
        assert config2.import_config(export_path) is True
        
        # インポートされた設定の確認
        assert config2.get('application.version') == '6.0.0'
        assert config2.get('custom.export_test') == 'exported'
    
    def test_get_config_info(self):
        """設定情報取得のテスト"""
        config = ConfigManager(self.config_path)
        
        info = config.get_config_info()
        
        assert 'config_path' in info
        assert 'file_exists' in info
        assert 'file_size' in info
        assert 'sections' in info
        assert 'validation_errors' in info
        
        assert info['config_path'] == str(self.config_path)
        assert info['file_exists'] is True
        assert info['file_size'] > 0
        assert len(info['sections']) >= 10
        assert isinstance(info['validation_errors'], list)
    
    def test_merge_configs(self):
        """設定マージのテスト"""
        config = ConfigManager(self.config_path)
        
        default = {
            'section1': {
                'key1': 'default1',
                'key2': 'default2'
            },
            'section2': {
                'nested': {
                    'value': 'default_nested'
                }
            }
        }
        
        user = {
            'section1': {
                'key1': 'user1',  # 上書き
                'key3': 'user3'   # 追加
            },
            'section2': {
                'nested': {
                    'value': 'user_nested',  # 上書き
                    'new': 'user_new'        # 追加
                }
            },
            'section3': {  # 新規セクション
                'new_section': 'value'
            }
        }
        
        merged = config._merge_configs(default, user)
        
        # 上書きされた値
        assert merged['section1']['key1'] == 'user1'
        # デフォルト値が残っている
        assert merged['section1']['key2'] == 'default2'
        # 追加された値
        assert merged['section1']['key3'] == 'user3'
        # ネストした上書き
        assert merged['section2']['nested']['value'] == 'user_nested'
        # ネストした追加
        assert merged['section2']['nested']['new'] == 'user_new'
        # 新規セクション
        assert merged['section3']['new_section'] == 'value'
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # 読み込み権限のないディレクトリをテスト
        with patch('builtins.open', side_effect=PermissionError):
            config = ConfigManager(self.config_path)
            # デフォルト設定が使用されることを確認
            assert config.get('application.version') == '1.0.0'
        
        # 保存エラーのテスト
        config = ConfigManager(self.config_path)
        with patch('builtins.open', side_effect=PermissionError):
            assert config.save() is False
        
        # エクスポートエラーのテスト
        with patch('builtins.open', side_effect=PermissionError):
            assert config.export_config(self.temp_dir / "error_test.json") is False
        
        # インポートエラーのテスト
        with patch('builtins.open', side_effect=FileNotFoundError):
            assert config.import_config(self.temp_dir / "nonexistent.json") is False
    
    def test_invalid_section_operations(self):
        """無効なセクション操作のテスト"""
        config = ConfigManager(self.config_path)
        
        # 存在しないセクションのリセット
        config.reset_to_default('nonexistent_section')
        # エラーが発生しないことを確認（警告ログのみ）
        
        # 辞書以外でのセクション設定
        config.set_section('test_section', 'not_a_dict')
        # 設定されないことを確認
        assert config.get('test_section') != 'not_a_dict'
    
    def test_string_representation(self):
        """文字列表現のテスト"""
        config = ConfigManager(self.config_path)
        
        str_repr = str(config)
        assert str(self.config_path) in str_repr
        assert 'ConfigManager' in str_repr
    
    @patch('src.data.config_manager.logging.getLogger')
    def test_logging_integration(self, mock_get_logger):
        """ログ統合のテスト"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        config = ConfigManager(self.config_path)
        
        # ログが呼び出されることを確認
        assert mock_logger.info.called or mock_logger.debug.called


class TestConfigManagerEdgeCases:
    """ConfigManagerのエッジケーステスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "edge_test_config.json"
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_empty_config_file(self):
        """空の設定ファイルのテスト"""
        # 空のファイルを作成
        self.config_path.touch()
        
        config = ConfigManager(self.config_path)
        # デフォルト設定が使用されることを確認
        assert config.get('application.version') == '1.0.0'
    
    def test_config_with_only_metadata(self):
        """メタデータのみの設定ファイルのテスト"""
        metadata_only = {
            '_metadata': {
                'created': '2024-01-01T00:00:00',
                'version': '1.0.0'
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as file:
            json.dump(metadata_only, file)
        
        config = ConfigManager(self.config_path)
        # デフォルト設定がマージされることを確認
        assert config.get('application.version') == '1.0.0'
    
    def test_deeply_nested_keys(self):
        """深くネストしたキーのテスト"""
        config = ConfigManager(self.config_path)
        
        # 深いネストの設定
        config.set('level1.level2.level3.level4.value', 'deep_value')
        assert config.get('level1.level2.level3.level4.value') == 'deep_value'
        
        # 中間レベルの取得
        level2 = config.get('level1.level2')
        assert isinstance(level2, dict)
        assert 'level3' in level2
    
    def test_special_characters_in_values(self):
        """特殊文字を含む値のテスト"""
        config = ConfigManager(self.config_path)
        
        special_values = {
            'unicode': 'こんにちは世界🌍',
            'newlines': 'line1\nline2\nline3',
            'quotes': 'He said "Hello" and she said \'Hi\'',
            'backslashes': 'C:\\Windows\\System32\\',
            'json_like': '{"key": "value", "number": 123}'
        }
        
        for key, value in special_values.items():
            config.set(f'special.{key}', value)
            assert config.get(f'special.{key}') == value
        
        # 保存・読み込みサイクルでの確認
        config.save()
        config2 = ConfigManager(self.config_path)
        
        for key, value in special_values.items():
            assert config2.get(f'special.{key}') == value
    
    def test_large_config_performance(self):
        """大きな設定ファイルのパフォーマンステスト"""
        config = ConfigManager(self.config_path)
        
        # 大量の設定項目を作成
        for i in range(1000):
            config.set(f'large_test.item_{i}', f'value_{i}')
        
        # パフォーマンス測定（実行時間のみ確認）
        import time
        
        start = time.time()
        config.save()
        save_time = time.time() - start
        
        start = time.time()
        config2 = ConfigManager(self.config_path)
        load_time = time.time() - start
        
        # 1秒以内で完了することを確認
        assert save_time < 1.0
        assert load_time < 1.0
        
        # データの整合性確認
        for i in range(0, 1000, 100):  # サンプリング確認
            assert config2.get(f'large_test.item_{i}') == f'value_{i}'