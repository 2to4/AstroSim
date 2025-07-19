"""
3Dレンダラーのモックオブジェクト

開発ルールに従い、モックの使用は最小限に抑え、外部依存のみをモック化します。
この場合、OpenGL/GPU依存のVispy部分のみをモック化します。
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from unittest.mock import Mock, MagicMock


class MockRenderer3D:
    """3Dレンダラーのモック"""
    
    def __init__(self):
        self.objects: Dict[str, Any] = {}
        self.scene_initialized = False
        self.camera_position = np.array([0.0, 0.0, 1000.0])
        self.camera_target = np.array([0.0, 0.0, 0.0])
        self.last_picked_object: Optional[str] = None
        self.render_count = 0
        
    def initialize_scene(self) -> None:
        """シーンの初期化（モック）"""
        self.scene_initialized = True
        
    def add_planet(self, planet_name: str, position: np.ndarray, 
                   radius: float, color: Tuple[float, float, float],
                   texture_path: Optional[str] = None) -> None:
        """惑星をシーンに追加（モック）"""
        self.objects[planet_name] = {
            'type': 'planet',
            'position': position.copy(),
            'radius': radius,
            'color': color,
            'texture_path': texture_path,
            'visible': True
        }
        
    def update_planet_position(self, planet_name: str, position: np.ndarray) -> None:
        """惑星の位置を更新（モック）"""
        if planet_name in self.objects:
            self.objects[planet_name]['position'] = position.copy()
        
    def add_orbit_line(self, planet_name: str, orbit_points: np.ndarray,
                      color: Tuple[float, float, float] = (0.5, 0.5, 0.5)) -> None:
        """軌道線を追加（モック）"""
        orbit_name = f"{planet_name}_orbit"
        self.objects[orbit_name] = {
            'type': 'orbit',
            'points': orbit_points.copy(),
            'color': color,
            'visible': True
        }
        
    def set_camera_position(self, position: np.ndarray, target: np.ndarray) -> None:
        """カメラ位置の設定（モック）"""
        self.camera_position = position.copy()
        self.camera_target = target.copy()
        
    def pick_object(self, screen_x: int, screen_y: int) -> Optional[str]:
        """オブジェクト選択（モック）"""
        # テスト用の簡単な実装
        # 実際のレイキャスティングの代わりに、画面座標から推定
        
        if not self.objects:
            return None
            
        # モックなので固定的な選択ロジック
        # 画面中央付近なら最初の惑星を選択
        if 400 <= screen_x <= 600 and 300 <= screen_y <= 500:
            for name, obj in self.objects.items():
                if obj['type'] == 'planet':
                    self.last_picked_object = name
                    return name
                    
        return None
        
    def render(self) -> None:
        """レンダリング実行（モック）"""
        self.render_count += 1
        
    def set_object_visibility(self, object_name: str, visible: bool) -> None:
        """オブジェクトの表示/非表示（モック）"""
        if object_name in self.objects:
            self.objects[object_name]['visible'] = visible
            
    def get_object_count(self) -> int:
        """オブジェクト数の取得"""
        return len(self.objects)
        
    def get_visible_object_count(self) -> int:
        """表示中オブジェクト数の取得"""
        return sum(1 for obj in self.objects.values() if obj['visible'])
        
    def clear_scene(self) -> None:
        """シーンのクリア"""
        self.objects.clear()
        self.scene_initialized = False
        self.render_count = 0


class MockSceneManager:
    """シーンマネージャーのモック"""
    
    def __init__(self):
        self.root_node = Mock()
        self.planet_nodes: Dict[str, Mock] = {}
        self.orbit_nodes: Dict[str, Mock] = {}
        
    def create_planet_node(self, planet_name: str) -> Mock:
        """惑星ノードの作成（モック）"""
        node = Mock()
        node.name = planet_name
        node.visible = True
        self.planet_nodes[planet_name] = node
        return node
        
    def create_orbit_node(self, planet_name: str) -> Mock:
        """軌道ノード作成（モック）"""
        node = Mock()
        node.name = f"{planet_name}_orbit"
        node.visible = True
        self.orbit_nodes[planet_name] = node
        return node
        
    def get_node(self, name: str) -> Optional[Mock]:
        """ノード取得"""
        if name in self.planet_nodes:
            return self.planet_nodes[name]
        for orbit_name, node in self.orbit_nodes.items():
            if node.name == name:
                return node
        return None


class MockCameraController:
    """カメラコントローラーのモック"""
    
    def __init__(self):
        self.azimuth = 0.0
        self.elevation = 30.0
        self.distance = 1000.0
        self.center = np.array([0.0, 0.0, 0.0])
        
    def rotate(self, delta_azimuth: float, delta_elevation: float) -> None:
        """カメラ回転（モック）"""
        self.azimuth += delta_azimuth
        self.elevation += delta_elevation
        
        # 仰角の制限
        self.elevation = max(-90, min(90, self.elevation))
        
    def zoom(self, factor: float) -> None:
        """ズーム（モック）"""
        self.distance *= factor
        self.distance = max(10.0, min(1e6, self.distance))
        
    def pan(self, delta_x: float, delta_y: float) -> None:
        """パン（モック）"""
        # 簡単な実装
        self.center[0] += delta_x
        self.center[1] += delta_y
        
    def focus_on_planet(self, position: np.ndarray, distance: float) -> None:
        """惑星へのフォーカス（モック）"""
        self.center = position.copy()
        self.distance = distance
        
    def reset_view(self) -> None:
        """ビューのリセット（モック）"""
        self.azimuth = 0.0
        self.elevation = 30.0
        self.distance = 1000.0
        self.center = np.array([0.0, 0.0, 0.0])
        
    def get_view_matrix(self) -> np.ndarray:
        """ビュー行列の取得（モック）"""
        # 簡単な4x4単位行列を返す
        return np.eye(4)


class MockTexture:
    """テクスチャのモック"""
    
    def __init__(self, path: str):
        self.path = path
        self.loaded = True
        self.width = 512
        self.height = 512
        
    def bind(self) -> None:
        """テクスチャバインド（モック）"""
        pass
        
    def unbind(self) -> None:
        """テクスチャアンバインド（モック）"""
        pass


class MockShader:
    """シェーダープログラムのモック"""
    
    def __init__(self, vertex_source: str, fragment_source: str):
        self.vertex_source = vertex_source
        self.fragment_source = fragment_source
        self.compiled = True
        self.uniforms: Dict[str, Any] = {}
        
    def use(self) -> None:
        """シェーダー使用（モック）"""
        pass
        
    def set_uniform(self, name: str, value: Any) -> None:
        """ユニフォーム変数設定（モック）"""
        self.uniforms[name] = value
        
    def get_uniform(self, name: str) -> Any:
        """ユニフォーム変数取得"""
        return self.uniforms.get(name)


def create_mock_vispy_canvas():
    """Vispyキャンバスのモック作成"""
    canvas = Mock()
    canvas.size = (800, 600)
    canvas.app = Mock()
    canvas.context = Mock()
    canvas.context.shared = Mock()
    
    # 基本的なイベント
    canvas.events = Mock()
    canvas.events.mouse_press = Mock()
    canvas.events.mouse_move = Mock()
    canvas.events.mouse_release = Mock()
    canvas.events.key_press = Mock()
    canvas.events.resize = Mock()
    
    return canvas


def create_mock_scene_canvas():
    """シーンキャンバスのモック作成"""
    canvas = create_mock_vispy_canvas()
    canvas.central_widget = Mock()
    canvas.central_widget.add_view = Mock()
    
    view = Mock()
    view.camera = Mock()
    view.scene = Mock()
    
    canvas.central_widget.add_view.return_value = view
    
    return canvas, view


class MockEventHandler:
    """イベントハンドラーのモック"""
    
    def __init__(self):
        self.events_received: List[Dict[str, Any]] = []
        
    def handle_mouse_press(self, event) -> None:
        """マウスプレスイベント（モック）"""
        self.events_received.append({
            'type': 'mouse_press',
            'pos': getattr(event, 'pos', (0, 0)),
            'button': getattr(event, 'button', 1)
        })
        
    def handle_mouse_move(self, event) -> None:
        """マウス移動イベント（モック）"""
        self.events_received.append({
            'type': 'mouse_move',
            'pos': getattr(event, 'pos', (0, 0)),
            'last_pos': getattr(event, 'last_pos', (0, 0))
        })
        
    def handle_key_press(self, event) -> None:
        """キープレスイベント（モック）"""
        self.events_received.append({
            'type': 'key_press',
            'key': getattr(event, 'key', ''),
            'text': getattr(event, 'text', '')
        })
        
    def clear_events(self) -> None:
        """イベント履歴のクリア"""
        self.events_received.clear()
        
    def get_event_count(self, event_type: str) -> int:
        """特定タイプのイベント数を取得"""
        return sum(1 for event in self.events_received if event['type'] == event_type)