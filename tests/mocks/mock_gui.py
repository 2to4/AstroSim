"""
GUIコンポーネントのモックオブジェクト

PyQt6のGUI依存部分のモック化を行います。
実際のウィジェット作成やイベント処理をテスト可能にします。
"""

from typing import Dict, List, Optional, Any, Callable
from unittest.mock import Mock, MagicMock, patch
import numpy as np


class MockQWidget:
    """QWidgetのモック"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.children: List['MockQWidget'] = []
        self.visible = True
        self.enabled = True
        self.geometry = (0, 0, 100, 100)  # x, y, width, height
        
        if parent:
            parent.children.append(self)
            
    def show(self) -> None:
        """ウィジェット表示"""
        self.visible = True
        
    def hide(self) -> None:
        """ウィジェット非表示"""
        self.visible = False
        
    def setEnabled(self, enabled: bool) -> None:
        """有効/無効設定"""
        self.enabled = enabled
        
    def isEnabled(self) -> bool:
        """有効状態取得"""
        return self.enabled
        
    def setGeometry(self, x: int, y: int, width: int, height: int) -> None:
        """ジオメトリ設定"""
        self.geometry = (x, y, width, height)


class MockQMainWindow(MockQWidget):
    """QMainWindowのモック"""
    
    def __init__(self):
        super().__init__()
        self.central_widget: Optional[MockQWidget] = None
        self.menu_bar: Optional['MockQMenuBar'] = None
        self.status_bar: Optional['MockQStatusBar'] = None
        self.title = ""
        self.closed = False
        
    def setCentralWidget(self, widget: MockQWidget) -> None:
        """中央ウィジェット設定"""
        self.central_widget = widget
        widget.parent = self
        
    def setWindowTitle(self, title: str) -> None:
        """ウィンドウタイトル設定"""
        self.title = title
        
    def menuBar(self) -> 'MockQMenuBar':
        """メニューバー取得"""
        if not self.menu_bar:
            self.menu_bar = MockQMenuBar(self)
        return self.menu_bar
        
    def statusBar(self) -> 'MockQStatusBar':
        """ステータスバー取得"""
        if not self.status_bar:
            self.status_bar = MockQStatusBar(self)
        return self.status_bar
        
    def close(self) -> None:
        """ウィンドウクローズ"""
        self.closed = True


class MockQMenuBar(MockQWidget):
    """QMenuBarのモック"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menus: Dict[str, 'MockQMenu'] = {}
        
    def addMenu(self, title: str) -> 'MockQMenu':
        """メニュー追加"""
        menu = MockQMenu(title, self)
        self.menus[title] = menu
        return menu


class MockQMenu(MockQWidget):
    """QMenuのモック"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.actions: List['MockQAction'] = []
        
    def addAction(self, text: str) -> 'MockQAction':
        """アクション追加"""
        action = MockQAction(text, self)
        self.actions.append(action)
        return action
        
    def addSeparator(self) -> None:
        """セパレーター追加"""
        separator = MockQAction("---separator---", self)
        separator.is_separator = True
        self.actions.append(separator)


class MockQAction:
    """QActionのモック"""
    
    def __init__(self, text: str, parent=None):
        self.text = text
        self.parent = parent
        self.enabled = True
        self.checkable = False
        self.checked = False
        self.is_separator = False
        self.triggered_callbacks: List[Callable] = []
        
    def setEnabled(self, enabled: bool) -> None:
        """有効/無効設定"""
        self.enabled = enabled
        
    def setCheckable(self, checkable: bool) -> None:
        """チェック可能設定"""
        self.checkable = checkable
        
    def setChecked(self, checked: bool) -> None:
        """チェック状態設定"""
        if self.checkable:
            self.checked = checked
            
    def triggered(self) -> Mock:
        """triggeredシグナルのモック"""
        signal = Mock()
        signal.connect = self._connect_triggered
        return signal
        
    def _connect_triggered(self, callback: Callable) -> None:
        """triggered接続"""
        self.triggered_callbacks.append(callback)
        
    def trigger(self) -> None:
        """アクション実行"""
        for callback in self.triggered_callbacks:
            callback()


class MockQStatusBar(MockQWidget):
    """QStatusBarのモック"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.message = ""
        
    def showMessage(self, message: str, timeout: int = 0) -> None:
        """メッセージ表示"""
        self.message = message


class MockQLabel(MockQWidget):
    """QLabelのモック"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.text = text
        
    def setText(self, text: str) -> None:
        """テキスト設定"""
        self.text = text
        
    def text(self) -> str:
        """テキスト取得"""
        return self.text


class MockQPushButton(MockQWidget):
    """QPushButtonのモック"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.text = text
        self.clicked_callbacks: List[Callable] = []
        
    def setText(self, text: str) -> None:
        """テキスト設定"""
        self.text = text
        
    def clicked(self) -> Mock:
        """clickedシグナルのモック"""
        signal = Mock()
        signal.connect = self._connect_clicked
        return signal
        
    def _connect_clicked(self, callback: Callable) -> None:
        """clicked接続"""
        self.clicked_callbacks.append(callback)
        
    def click(self) -> None:
        """ボタンクリック"""
        for callback in self.clicked_callbacks:
            callback()


class MockQSlider(MockQWidget):
    """QSliderのモック"""
    
    def __init__(self, orientation=1, parent=None):  # 1 = Horizontal
        super().__init__(parent)
        self.orientation = orientation
        self.minimum_value = 0
        self.maximum_value = 100
        self.current_value = 0
        self.value_changed_callbacks: List[Callable] = []
        
    def setMinimum(self, minimum: int) -> None:
        """最小値設定"""
        self.minimum_value = minimum
        
    def setMaximum(self, maximum: int) -> None:
        """最大値設定"""
        self.maximum_value = maximum
        
    def setValue(self, value: int) -> None:
        """値設定"""
        self.current_value = max(self.minimum_value, min(self.maximum_value, value))
        
    def value(self) -> int:
        """値取得"""
        return self.current_value
        
    def valueChanged(self) -> Mock:
        """valueChangedシグナルのモック"""
        signal = Mock()
        signal.connect = self._connect_value_changed
        return signal
        
    def _connect_value_changed(self, callback: Callable) -> None:
        """valueChanged接続"""
        self.value_changed_callbacks.append(callback)
        
    def _emit_value_changed(self) -> None:
        """valueChangedシグナル発行"""
        for callback in self.value_changed_callbacks:
            callback(self.current_value)


class MockQTextBrowser(MockQWidget):
    """QTextBrowserのモック"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_content = ""
        self.plain_text = ""
        
    def setHtml(self, html: str) -> None:
        """HTML設定"""
        self.html_content = html
        # 簡単なHTMLからプレーンテキスト変換
        import re
        self.plain_text = re.sub('<[^<]+?>', '', html)
        
    def setPlainText(self, text: str) -> None:
        """プレーンテキスト設定"""
        self.plain_text = text
        self.html_content = text
        
    def toHtml(self) -> str:
        """HTML取得"""
        return self.html_content
        
    def toPlainText(self) -> str:
        """プレーンテキスト取得"""
        return self.plain_text
        
    def clear(self) -> None:
        """内容クリア"""
        self.html_content = ""
        self.plain_text = ""


class MockQVBoxLayout:
    """QVBoxLayoutのモック"""
    
    def __init__(self):
        self.widgets: List[MockQWidget] = []
        
    def addWidget(self, widget: MockQWidget) -> None:
        """ウィジェット追加"""
        self.widgets.append(widget)
        
    def addLayout(self, layout: 'MockQVBoxLayout') -> None:
        """レイアウト追加"""
        self.widgets.extend(layout.widgets)


class MockQHBoxLayout:
    """QHBoxLayoutのモック"""
    
    def __init__(self):
        self.widgets: List[MockQWidget] = []
        
    def addWidget(self, widget: MockQWidget) -> None:
        """ウィジェット追加"""
        self.widgets.append(widget)
        
    def addLayout(self, layout: 'MockQHBoxLayout') -> None:
        """レイアウト追加"""
        self.widgets.extend(layout.widgets)


class MockQApplication:
    """QApplicationのモック"""
    
    def __init__(self, argv: List[str]):
        self.argv = argv
        self.exit_code = 0
        self.running = False
        
    def exec(self) -> int:
        """アプリケーション実行"""
        self.running = True
        return self.exit_code
        
    def quit(self) -> None:
        """アプリケーション終了"""
        self.running = False
        
    def exit(self, exit_code: int = 0) -> None:
        """アプリケーション終了（終了コード指定）"""
        self.exit_code = exit_code
        self.running = False


class MockQTimer:
    """QTimerのモック"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.interval_ms = 1000
        self.single_shot = False
        self.active = False
        self.timeout_callbacks: List[Callable] = []
        
    def setInterval(self, ms: int) -> None:
        """間隔設定"""
        self.interval_ms = ms
        
    def setSingleShot(self, single_shot: bool) -> None:
        """シングルショット設定"""
        self.single_shot = single_shot
        
    def start(self) -> None:
        """タイマー開始"""
        self.active = True
        
    def stop(self) -> None:
        """タイマー停止"""
        self.active = False
        
    def timeout(self) -> Mock:
        """timeoutシグナルのモック"""
        signal = Mock()
        signal.connect = self._connect_timeout
        return signal
        
    def _connect_timeout(self, callback: Callable) -> None:
        """timeout接続"""
        self.timeout_callbacks.append(callback)
        
    def _emit_timeout(self) -> None:
        """timeoutシグナル発行（テスト用）"""
        for callback in self.timeout_callbacks:
            callback()


def create_mock_qt_app():
    """モックQtアプリケーションの作成"""
    import sys
    return MockQApplication(sys.argv)


def create_mock_main_window():
    """モックメインウィンドウの作成"""
    return MockQMainWindow()


class MockSignalEmitter:
    """Qtシグナルエミッターのモック"""
    
    def __init__(self):
        self.connected_slots: List[Callable] = []
        
    def connect(self, slot: Callable) -> None:
        """スロット接続"""
        self.connected_slots.append(slot)
        
    def disconnect(self, slot: Optional[Callable] = None) -> None:
        """スロット切断"""
        if slot is None:
            self.connected_slots.clear()
        elif slot in self.connected_slots:
            self.connected_slots.remove(slot)
            
    def emit(self, *args, **kwargs) -> None:
        """シグナル発行"""
        for slot in self.connected_slots:
            slot(*args, **kwargs)


# PyQt6の主要クラスをモックに置き換えるパッチャー
def patch_pyqt6():
    """PyQt6のモック化パッチ"""
    return patch.multiple(
        'PyQt6.QtWidgets',
        QApplication=MockQApplication,
        QMainWindow=MockQMainWindow,
        QWidget=MockQWidget,
        QLabel=MockQLabel,
        QPushButton=MockQPushButton,
        QSlider=MockQSlider,
        QTextBrowser=MockQTextBrowser,
        QVBoxLayout=MockQVBoxLayout,
        QHBoxLayout=MockQHBoxLayout,
        QMenuBar=MockQMenuBar,
        QStatusBar=MockQStatusBar,
    )