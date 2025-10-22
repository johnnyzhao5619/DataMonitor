"""主题管理与主题定义模块。"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from PyQt5 import QtGui, QtWidgets


PaletteFactory = Callable[[], QtGui.QPalette]


@dataclass(frozen=True)
class ThemeDefinition:
    """封装单个主题的调色板与样式表定义。"""

    name: str
    palette_factory: PaletteFactory
    stylesheet: str

    def create_palette(self) -> QtGui.QPalette:
        """构造调色板副本，避免外部修改共享状态。"""

        palette = self.palette_factory()
        return QtGui.QPalette(palette)


class ThemeManager:
    """负责注册与切换主题的管理器。"""

    def __init__(self, app: Optional[QtWidgets.QApplication] = None) -> None:
        self._app = app or QtWidgets.QApplication.instance()
        if self._app is None:
            raise RuntimeError("ThemeManager 需要有效的 QApplication 实例")

        self._themes: "OrderedDict[str, ThemeDefinition]" = OrderedDict()
        self._current: Optional[str] = None

    def register(self, theme: ThemeDefinition) -> None:
        """注册单个主题，如果名称重复则覆盖旧值。"""

        self._themes[theme.name] = theme

    def register_many(self, themes: Iterable[ThemeDefinition]) -> None:
        """按顺序批量注册主题。"""

        for theme in themes:
            self.register(theme)

    def available_themes(self) -> list[str]:
        return list(self._themes.keys())

    def current_theme_name(self) -> Optional[str]:
        return self._current

    def current_theme(self) -> Optional[ThemeDefinition]:
        if self._current is None:
            return None
        return self._themes.get(self._current)

    def apply_theme(self, name: str) -> ThemeDefinition:
        """应用指定名称的主题，同时刷新已存在的控件。"""

        if name not in self._themes:
            raise KeyError(f"未注册主题: {name}")

        theme = self._themes[name]
        palette = theme.create_palette()

        self._app.setPalette(palette)
        self._app.setStyleSheet(theme.stylesheet)
        self._current = name
        self._app.setProperty("currentTheme", name)

        style = self._app.style()
        style.unpolish(self._app)
        style.polish(self._app)

        for widget in self._app.allWidgets():
            widget.setPalette(palette)
            style.unpolish(widget)
            style.polish(widget)
            widget.update()

        return theme


def _create_workspace_light_palette() -> QtGui.QPalette:
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#F3F2F1"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#201F1E"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#F7F6F3"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#201F1E"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#201F1E"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#201F1E"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#6264A7"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("#C50F1F"))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor("#605E5C"))
    palette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor("#414043"))
    palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#605E5C"))
    return palette


def _create_workspace_dark_palette() -> QtGui.QPalette:
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#1F1F24"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#F3F2F1"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#1F1F24"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#2D2C30"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#2D2C30"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#F3F2F1"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#F3F2F1"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#2D2C30"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#F3F2F1"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#8B8CC7"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#1F1F24"))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("#F1707B"))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor("#C8C6C4"))
    palette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor("#A19F9D"))
    palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#A19F9D"))
    return palette


_LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #F3F2F1;
}
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #201F1E;
}
QPushButton {
    background-color: #6264A7;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}
QPushButton[category="navigation"] {
    background-color: transparent;
    color: #201F1E;
    border-radius: 8px;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
}
QPushButton[category="navigation"]:hover {
    background-color: #E1DFDD;
    color: #201F1E;
}
QPushButton[category="navigation"]:checked {
    background-color: #C8C6C4;
    color: #201F1E;
}
QPushButton:pressed {
    background-color: #33344A;
}
QPushButton:disabled {
    background-color: #E1DFDD;
    color: #A19F9D;
}
QFrame#navigationBar {
    background-color: #F3F2F1;
    border-right: 1px solid #E1DFDD;
}
QFrame[role="card"], QWidget[role="card"] {
    background: white;
    border: 1px solid #E1DFDD;
    border-radius: 10px;
}
QFrame[role="card"] QLabel[role="cardTitle"], QWidget[role="card"] QLabel[role="cardTitle"] {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
QLabel[role="heading"] {
    font-size: 18px;
    font-weight: 600;
}
QLabel[role="hint"] {
    color: #605E5C;
}
QLabel[role="error"] {
    color: #C50F1F;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextBrowser, QListWidget {
    background: white;
    border: 1px solid #C8C6C4;
    border-radius: 6px;
    padding: 6px;
}
QPlainTextEdit, QTextBrowser {
    padding: 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #C8C6C4;
    selection-background-color: #6264A7;
    selection-color: white;
}
QStatusBar {
    background: #E1DFDD;
    border-top: 1px solid #C8C6C4;
}
QTabWidget::pane {
    border: 1px solid #C8C6C4;
    border-radius: 6px;
}
QTabBar::tab {
    background: #E9E9F0;
    border: 1px solid #C8C6C4;
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: white;
    color: #201F1E;
}
QScrollArea {
    background: transparent;
    border: none;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QSplitter::handle {
    background-color: #E1DFDD;
}
QToolTip {
    color: #201F1E;
    background-color: #FFFFFF;
    border: 1px solid #C8C6C4;
}
"""


_DARK_STYLESHEET = """
QMainWindow {
    background-color: #1F1F24;
}
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #F3F2F1;
}
QPushButton {
    background-color: #464775;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}
QPushButton[category="navigation"] {
    background-color: transparent;
    color: #F3F2F1;
    border-radius: 8px;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
}
QPushButton[category="navigation"]:hover {
    background-color: #3B3A39;
    color: #FFFFFF;
}
QPushButton[category="navigation"]:checked {
    background-color: #3F3F46;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #32315A;
}
QPushButton:disabled {
    background-color: #2D2C3A;
    color: #8A8886;
}
QFrame#navigationBar {
    background-color: #252526;
    border-right: 1px solid #3B3A39;
}
QFrame[role="card"], QWidget[role="card"] {
    background: #2D2C30;
    border: 1px solid #3B3A39;
    border-radius: 10px;
}
QFrame[role="card"] QLabel[role="cardTitle"], QWidget[role="card"] QLabel[role="cardTitle"] {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #F3F2F1;
}
QLabel[role="heading"] {
    font-size: 18px;
    font-weight: 600;
    color: #FFFFFF;
}
QLabel[role="hint"] {
    color: #C8C6C4;
}
QLabel[role="error"] {
    color: #F1707B;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextBrowser, QListWidget {
    background: #1F1F24;
    border: 1px solid #3B3A39;
    border-radius: 6px;
    padding: 6px;
    color: #F3F2F1;
}
QPlainTextEdit, QTextBrowser {
    padding: 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: #2D2C30;
    border: 1px solid #3B3A39;
    selection-background-color: #8B8CC7;
    selection-color: #1F1F24;
}
QStatusBar {
    background: #2D2C30;
    border-top: 1px solid #3B3A39;
    color: #F3F2F1;
}
QTabWidget::pane {
    border: 1px solid #3B3A39;
    border-radius: 6px;
}
QTabBar::tab {
    background: #302F3A;
    border: 1px solid #3B3A39;
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #C8C6C4;
}
QTabBar::tab:selected {
    background: #1F1F24;
    color: #FFFFFF;
}
QScrollArea {
    background: transparent;
    border: none;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: #F3F2F1;
}
QSplitter::handle {
    background-color: #3B3A39;
}
QToolTip {
    color: #F3F2F1;
    background-color: #2D2C30;
    border: 1px solid #3B3A39;
}
QListWidget::item:selected {
    background-color: #8B8CC7;
    color: #1F1F24;
}
"""


workspace_light = ThemeDefinition(
    name="Workspace Light",
    palette_factory=_create_workspace_light_palette,
    stylesheet=_LIGHT_STYLESHEET,
)


workspace_dark = ThemeDefinition(
    name="Workspace Dark",
    palette_factory=_create_workspace_dark_palette,
    stylesheet=_DARK_STYLESHEET,
)


__all__ = [
    "ThemeDefinition",
    "ThemeManager",
    "workspace_light",
    "workspace_dark",
]
