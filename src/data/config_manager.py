"""
設定管理クラスの実装

アプリケーション設定の読み込み、保存、
デフォルト値の管理などを行います。
"""

import json
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from datetime import datetime


class ConfigManager:
    """
    アプリケーション設定を管理するクラス
    
    設定ファイルの読み込み、保存、デフォルト値の提供、
    設定の検証などを行います。
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        設定管理の初期化
        
        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルト使用）
        """
        # 設定ファイルパスの設定
        if config_path is None:
            # ユーザーホームディレクトリの設定フォルダを使用
            config_dir = Path.home() / ".astrosim"
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / "config.json"
        else:
            self.config_path = config_path
        
        # 設定データ
        self._config: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = {}
        
        # ロガー設定
        self.logger = logging.getLogger(__name__)
        
        # デフォルト設定の初期化
        self._initialize_defaults()
        
        # 設定ファイルの読み込み
        self._load_config()
    
    def _initialize_defaults(self) -> None:
        """デフォルト設定の初期化"""
        self._default_config = {
            # アプリケーション設定
            "application": {
                "version": "1.0.0",
                "language": "ja",
                "theme": "default",
                "auto_save": True,
                "backup_count": 5
            },
            
            # ウィンドウ設定
            "window": {
                "width": 1600,
                "height": 1000,
                "maximized": False,
                "fullscreen": False,
                "remember_position": True,
                "x": 100,
                "y": 100
            },
            
            # シミュレーション設定
            "simulation": {
                "default_time_scale": 1.0,
                "auto_play": False,
                "fps": 60,
                "physics_precision": "high",
                "integration_method": "rk4"
            },
            
            # 表示設定
            "display": {
                "show_orbits": True,
                "show_labels": True,
                "show_axes": False,
                "show_grid": False,
                "show_trails": False,
                "planet_scale": 10.0,
                "distance_scale": 1.0,
                "background_color": [0.0, 0.0, 0.0, 1.0],  # 完全な黒
                "anti_aliasing": True,
                "vsync": True
            },
            
            # カメラ設定
            "camera": {
                "default_distance": 80.0,  # 外惑星も含めた太陽系全体が見える距離
                "default_elevation": 30.0,
                "default_azimuth": 30.0,
                "movement_speed": 1.0,
                "rotation_speed": 1.0,
                "zoom_speed": 1.1,
                "smooth_movement": True
            },
            
            # データ設定
            "data": {
                "default_data_path": "src/data/planet_data.json",
                "auto_reload": False,
                "cache_enabled": True,
                "cache_size_mb": 100
            },
            
            # パフォーマンス設定
            "performance": {
                "max_trail_points": 1000,
                "orbit_resolution": 360,
                "adaptive_quality": True,
                "gpu_acceleration": True,
                "multi_threading": True
            },
            
            # UI設定
            "ui": {
                "control_panel_width": 300,
                "info_panel_height": 200,
                "font_size": 10,
                "icon_size": 16,
                "toolbar_visible": True,
                "status_bar_visible": True
            },
            
            # キーボードショートカット
            "shortcuts": {
                "play_pause": "Space",
                "reset_view": "R",
                "toggle_orbits": "O",
                "toggle_labels": "L",
                "fullscreen": "F11",
                "screenshot": "F12",
                "quit": "Ctrl+Q"
            },
            
            # ログ設定
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_file_path": "logs/astrosim.log",
                "max_log_size_mb": 10,
                "backup_count": 3
            }
        }
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        import copy
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    user_config = json.load(file)
                
                # デフォルト設定にユーザー設定をマージ
                self._config = self._merge_configs(copy.deepcopy(self._default_config), user_config)
                
                self.logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                # デフォルト設定を使用
                self._config = copy.deepcopy(self._default_config)
                self.logger.info("デフォルト設定を使用します")
                
                # デフォルト設定ファイルを作成
                self._create_default_config_file()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイルの解析エラー: {e}")
            self._config = copy.deepcopy(self._default_config)
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
            self._config = copy.deepcopy(self._default_config)
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """設定をマージ（ユーザー設定を優先）"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 再帰的にマージ
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # ユーザー設定で上書き
                merged[key] = value
        
        return merged
    
    def _create_default_config_file(self) -> None:
        """デフォルト設定ファイルを作成"""
        try:
            # ディレクトリを作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # メタデータを追加
            config_with_meta = {
                "_metadata": {
                    "created": datetime.now().isoformat(),
                    "version": self._default_config["application"]["version"],
                    "description": "AstroSim アプリケーション設定ファイル"
                },
                **self._default_config
            }
            
            # ファイルに保存
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_with_meta, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"デフォルト設定ファイルを作成しました: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"設定ファイル作成エラー: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応）
            default: デフォルト値
            
        Returns:
            設定値
        """
        try:
            # ドット記法をサポート（例: "display.show_orbits"）
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"設定取得エラー: {key}, {e}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        設定値を更新
        
        Args:
            key: 設定キー（ドット記法対応）
            value: 設定値
        """
        try:
            # ドット記法をサポート
            keys = key.split('.')
            config = self._config
            
            # 最後のキー以外は辞書を作成
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
            
            # 最後のキーに値を設定
            config[keys[-1]] = value
            
            self.logger.debug(f"設定を更新しました: {key} = {value}")
            
        except Exception as e:
            self.logger.error(f"設定更新エラー: {key}, {e}")
    
    def save(self) -> bool:
        """
        設定をファイルに保存
        
        Returns:
            保存成功したかどうか
        """
        try:
            # バックアップ作成
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.bak')
                backup_path.write_bytes(self.config_path.read_bytes())
            
            # メタデータを追加
            config_with_meta = {
                "_metadata": {
                    "saved": datetime.now().isoformat(),
                    "version": self.get("application.version", "1.0.0")
                },
                **self._config
            }
            
            # ファイルに保存
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_with_meta, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定を保存しました: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
            return False
    
    def reset_to_default(self, section: Optional[str] = None) -> None:
        """
        設定をデフォルトにリセット
        
        Args:
            section: リセットするセクション（Noneの場合は全体）
        """
        import copy
        
        if section is None:
            # 全体をリセット
            self._config = copy.deepcopy(self._default_config)
            self.logger.info("全設定をデフォルトにリセットしました")
        else:
            # 特定のセクションのみリセット
            if section in self._default_config:
                self._config[section] = copy.deepcopy(self._default_config[section])
                self.logger.info(f"設定セクション '{section}' をデフォルトにリセットしました")
            else:
                self.logger.warning(f"設定セクション '{section}' が見つかりません")
    
    def validate_config(self) -> List[str]:
        """
        設定の妥当性を検証
        
        Returns:
            エラーメッセージのリスト
        """
        errors = []
        
        try:
            # 基本的な型チェック
            if not isinstance(self._config, dict):
                errors.append("設定のルートオブジェクトが辞書ではありません")
                return errors
            
            # 数値範囲チェック
            numeric_ranges = {
                "window.width": (800, 4000),
                "window.height": (600, 3000),
                "simulation.fps": (10, 120),
                "camera.default_distance": (0.1, 100.0),
                "performance.max_trail_points": (100, 10000)
            }
            
            for key, (min_val, max_val) in numeric_ranges.items():
                value = self.get(key)
                if value is not None:
                    if not isinstance(value, (int, float)):
                        errors.append(f"{key}: 数値である必要があります")
                    elif not (min_val <= value <= max_val):
                        errors.append(f"{key}: {min_val}から{max_val}の範囲である必要があります")
            
            # 色設定の検証
            color_keys = ["display.background_color"]
            for key in color_keys:
                color = self.get(key)
                if color is not None:
                    if not isinstance(color, list) or len(color) != 4:
                        errors.append(f"{key}: RGBA形式（4要素のリスト）である必要があります")
                    elif not all(0.0 <= c <= 1.0 for c in color):
                        errors.append(f"{key}: 各要素は0.0から1.0の範囲である必要があります")
            
            # パス設定の検証
            path_keys = ["data.default_data_path", "logging.log_file_path"]
            for key in path_keys:
                path_str = self.get(key)
                if path_str is not None:
                    try:
                        Path(path_str)
                    except Exception:
                        errors.append(f"{key}: 無効なパス形式です")
            
        except Exception as e:
            errors.append(f"設定検証中にエラーが発生しました: {e}")
        
        return errors
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        設定セクション全体を取得
        
        Args:
            section: セクション名
            
        Returns:
            セクションの設定辞書
        """
        return self._config.get(section, {}).copy()
    
    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        設定セクション全体を更新
        
        Args:
            section: セクション名
            values: 設定値の辞書
        """
        if not isinstance(values, dict):
            self.logger.error(f"セクション '{section}' の値は辞書である必要があります")
            return
        
        self._config[section] = values.copy()
        self.logger.info(f"設定セクション '{section}' を更新しました")
    
    def get_all_sections(self) -> List[str]:
        """全設定セクション名を取得"""
        return [key for key in self._config.keys() if not key.startswith('_')]
    
    def export_config(self, export_path: Path) -> bool:
        """
        設定をエクスポート
        
        Args:
            export_path: エクスポート先パス
            
        Returns:
            エクスポート成功したかどうか
        """
        try:
            export_data = {
                "_export_info": {
                    "exported": datetime.now().isoformat(),
                    "source": str(self.config_path),
                    "version": self.get("application.version", "1.0.0")
                },
                **self._config
            }
            
            with open(export_path, 'w', encoding='utf-8') as file:
                json.dump(export_data, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定をエクスポートしました: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定エクスポートエラー: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """
        設定をインポート
        
        Args:
            import_path: インポート元パス
            
        Returns:
            インポート成功したかどうか
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as file:
                imported_config = json.load(file)
            
            # メタデータを除去
            imported_config.pop('_export_info', None)
            imported_config.pop('_metadata', None)
            
            # 設定をマージ
            self._config = self._merge_configs(self._default_config, imported_config)
            
            # 検証
            errors = self.validate_config()
            if errors:
                self.logger.warning(f"インポートした設定に問題があります: {errors}")
            
            self.logger.info(f"設定をインポートしました: {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定インポートエラー: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """設定情報を取得"""
        return {
            'config_path': str(self.config_path),
            'file_exists': self.config_path.exists(),
            'file_size': self.config_path.stat().st_size if self.config_path.exists() else 0,
            'sections': self.get_all_sections(),
            'validation_errors': self.validate_config()
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"ConfigManager (パス: {self.config_path}, セクション: {len(self.get_all_sections())})"