"""
データ層のモックオブジェクト

ファイルI/O、ネットワーク、データベースアクセスなどの外部依存をモック化します。
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import numpy as np


class MockFileSystem:
    """ファイルシステムのモック"""
    
    def __init__(self):
        self.files: Dict[str, str] = {}  # path -> content
        self.directories: set = set()
        
    def exists(self, path: str) -> bool:
        """ファイル/ディレクトリ存在確認"""
        return path in self.files or path in self.directories
        
    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """テキストファイル読み込み"""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
        
    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """テキストファイル書き込み"""
        self.files[path] = content
        
        # ディレクトリの自動作成
        parent_dir = str(Path(path).parent)
        if parent_dir != '.':
            self.directories.add(parent_dir)
            
    def mkdir(self, path: str, parents: bool = False) -> None:
        """ディレクトリ作成"""
        self.directories.add(path)
        
        if parents:
            # 親ディレクトリも作成
            current_path = Path(path)
            while current_path.parent != current_path:
                self.directories.add(str(current_path.parent))
                current_path = current_path.parent
                
    def remove(self, path: str) -> None:
        """ファイル削除"""
        if path in self.files:
            del self.files[path]
        elif path in self.directories:
            self.directories.remove(path)
            
    def list_files(self, directory: str) -> List[str]:
        """ディレクトリ内ファイル一覧"""
        return [f for f in self.files.keys() if f.startswith(directory)]


class MockPlanetRepository:
    """惑星データリポジトリのモック"""
    
    def __init__(self):
        self.planet_data = {
            "地球": {
                "name": "地球",
                "name_en": "Earth",
                "mass": 5.972e24,
                "radius": 6371.0,
                "color": [0.0, 0.5, 1.0],
                "orbital_elements": {
                    "semi_major_axis": 1.0,
                    "eccentricity": 0.0167,
                    "inclination": 0.0,
                    "longitude_of_ascending_node": 0.0,
                    "argument_of_perihelion": 0.0,
                    "mean_anomaly_at_epoch": 0.0,
                    "epoch": 2451545.0
                }
            },
            "火星": {
                "name": "火星",
                "name_en": "Mars",
                "mass": 6.39e23,
                "radius": 3389.5,
                "color": [1.0, 0.5, 0.0],
                "orbital_elements": {
                    "semi_major_axis": 1.524,
                    "eccentricity": 0.0934,
                    "inclination": 1.85,
                    "longitude_of_ascending_node": 49.56,
                    "argument_of_perihelion": 286.5,
                    "mean_anomaly_at_epoch": 19.39,
                    "epoch": 2451545.0
                }
            }
        }
        self.load_call_count = 0
        self.save_call_count = 0
        
    def load_planet_data(self, file_path: str) -> Dict[str, Any]:
        """惑星データ読み込み（モック）"""
        self.load_call_count += 1
        return {"planets": list(self.planet_data.values())}
        
    def save_planet_data(self, file_path: str, data: Dict[str, Any]) -> None:
        """惑星データ保存（モック）"""
        self.save_call_count += 1
        # データの更新
        if "planets" in data:
            for planet in data["planets"]:
                self.planet_data[planet["name"]] = planet
                
    def get_planet_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """名前で惑星データを取得"""
        return self.planet_data.get(name)
        
    def add_planet(self, planet_data: Dict[str, Any]) -> None:
        """惑星データ追加"""
        self.planet_data[planet_data["name"]] = planet_data
        
    def remove_planet(self, name: str) -> None:
        """惑星データ削除"""
        if name in self.planet_data:
            del self.planet_data[name]
            
    def get_all_planets(self) -> List[Dict[str, Any]]:
        """全惑星データ取得"""
        return list(self.planet_data.values())


class MockConfigManager:
    """設定管理のモック"""
    
    def __init__(self):
        self.config = {
            "application": {
                "window_size": [1920, 1080],
                "fullscreen": False,
                "language": "ja"
            },
            "simulation": {
                "start_date": "2024-01-01T00:00:00",
                "time_scale": 1.0,
                "show_orbits": True,
                "show_labels": True
            },
            "graphics": {
                "antialiasing": 4,
                "texture_quality": "high",
                "shadow_quality": "medium"
            }
        }
        self.load_call_count = 0
        self.save_call_count = 0
        
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """設定読み込み（モック）"""
        self.load_call_count += 1
        return self.config.copy()
        
    def save_config(self, file_path: str, config: Dict[str, Any]) -> None:
        """設定保存（モック）"""
        self.save_call_count += 1
        self.config.update(config)
        
    def get(self, key: str, default: Any = None) -> Any:
        """設定値取得"""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
                
        return current
        
    def set(self, key: str, value: Any) -> None:
        """設定値設定"""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
            
        current[keys[-1]] = value


class MockDataLoader:
    """データローダーのモック"""
    
    def __init__(self):
        self.load_attempts = []
        self.load_errors = []
        
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """JSON読み込み（モック）"""
        self.load_attempts.append(('json', file_path))
        
        # 特定のファイルでエラーをシミュレート
        if 'error' in file_path:
            error = FileNotFoundError(f"Mock error loading {file_path}")
            self.load_errors.append(error)
            raise error
            
        # サンプルデータを返す
        if 'planet' in file_path.lower():
            return {
                "planets": [
                    {
                        "name": "テスト惑星",
                        "mass": 1.0e24,
                        "radius": 1000.0,
                        "orbital_elements": {
                            "semi_major_axis": 1.0,
                            "eccentricity": 0.0,
                            "inclination": 0.0,
                            "longitude_of_ascending_node": 0.0,
                            "argument_of_perihelion": 0.0,
                            "mean_anomaly_at_epoch": 0.0,
                            "epoch": 2451545.0
                        }
                    }
                ]
            }
        elif 'config' in file_path.lower():
            return {
                "application": {"language": "ja"},
                "simulation": {"time_scale": 1.0}
            }
        else:
            return {}
            
    def save_json(self, file_path: str, data: Dict[str, Any]) -> None:
        """JSON保存（モック）"""
        self.load_attempts.append(('save_json', file_path))
        
        # 特定のファイルでエラーをシミュレート
        if 'readonly' in file_path:
            error = PermissionError(f"Mock permission error saving {file_path}")
            self.load_errors.append(error)
            raise error
            
    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """CSV読み込み（モック）"""
        self.load_attempts.append(('csv', file_path))
        
        # サンプルCSVデータ
        return [
            {"name": "Mercury", "distance": "0.39", "period": "88"},
            {"name": "Venus", "distance": "0.72", "period": "225"},
            {"name": "Earth", "distance": "1.0", "period": "365"}
        ]


class MockTextureLoader:
    """テクスチャローダーのモック"""
    
    def __init__(self):
        self.loaded_textures: Dict[str, 'MockTexture'] = {}
        self.load_attempts = []
        
    def load_texture(self, file_path: str) -> 'MockTexture':
        """テクスチャ読み込み（モック）"""
        self.load_attempts.append(file_path)
        
        if file_path not in self.loaded_textures:
            if 'missing' in file_path:
                raise FileNotFoundError(f"Texture not found: {file_path}")
                
            # モックテクスチャを作成
            texture = MockTexture(file_path)
            self.loaded_textures[file_path] = texture
            
        return self.loaded_textures[file_path]
        
    def get_texture(self, file_path: str) -> Optional['MockTexture']:
        """テクスチャ取得"""
        return self.loaded_textures.get(file_path)
        
    def clear_cache(self) -> None:
        """テクスチャキャッシュクリア"""
        self.loaded_textures.clear()


class MockTexture:
    """テクスチャのモック"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.width = 512
        self.height = 512
        self.format = "RGB"
        self.loaded = True
        self.data = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
        
    def get_size(self) -> tuple:
        """サイズ取得"""
        return (self.width, self.height)
        
    def get_data(self) -> np.ndarray:
        """データ取得"""
        return self.data


class MockNetworkLoader:
    """ネットワークローダーのモック"""
    
    def __init__(self):
        self.request_history = []
        self.responses = {}
        self.default_response = {"status": "success", "data": {}}
        
    def set_response(self, url: str, response: Dict[str, Any]) -> None:
        """レスポンス設定"""
        self.responses[url] = response
        
    def get(self, url: str, timeout: float = 10.0) -> Dict[str, Any]:
        """GET リクエスト（モック）"""
        self.request_history.append(('GET', url, timeout))
        
        # ネットワークエラーのシミュレート
        if 'error' in url:
            raise ConnectionError(f"Mock network error for {url}")
            
        # 設定されたレスポンスまたはデフォルトを返す
        return self.responses.get(url, self.default_response)
        
    def post(self, url: str, data: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """POST リクエスト（モック）"""
        self.request_history.append(('POST', url, data, timeout))
        
        return self.responses.get(url, self.default_response)


def create_temporary_data_files():
    """テスト用の一時データファイル作成"""
    temp_dir = tempfile.mkdtemp()
    temp_dir_path = Path(temp_dir)
    
    # 惑星データファイル
    planet_data = {
        "planets": [
            {
                "name": "地球",
                "name_en": "Earth",
                "mass": 5.972e24,
                "radius": 6371.0,
                "orbital_elements": {
                    "semi_major_axis": 1.0,
                    "eccentricity": 0.0167,
                    "inclination": 0.0,
                    "longitude_of_ascending_node": 0.0,
                    "argument_of_perihelion": 0.0,
                    "mean_anomaly_at_epoch": 0.0,
                    "epoch": 2451545.0
                }
            }
        ]
    }
    
    planet_file = temp_dir_path / "planets.json"
    with open(planet_file, 'w', encoding='utf-8') as f:
        json.dump(planet_data, f, indent=2, ensure_ascii=False)
        
    # 設定ファイル
    config_data = {
        "application": {
            "language": "ja",
            "window_size": [1920, 1080]
        },
        "simulation": {
            "time_scale": 1.0
        }
    }
    
    config_file = temp_dir_path / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
        
    return {
        'temp_dir': temp_dir_path,
        'planet_file': planet_file,
        'config_file': config_file
    }


def cleanup_temporary_files(temp_files: Dict[str, Path]) -> None:
    """一時ファイルのクリーンアップ"""
    import shutil
    try:
        shutil.rmtree(temp_files['temp_dir'])
    except Exception:
        pass  # クリーンアップエラーは無視