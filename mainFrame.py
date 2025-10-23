"""应用入口窗口定义。"""

import queue
from importlib import import_module
from typing import TYPE_CHECKING

from PyQt5 import QtWidgets

from controllers import MainWindowController
from ui.main_window import MainWindowUI

import apiMonitor  # 用于兼容现有测试
import configuration
import logRecorder

if TYPE_CHECKING:
    from ui.theme import ThemeDefinition, ThemeManager


def _load_theme_resources() -> tuple["ThemeManager", tuple["ThemeDefinition", ...]]:
    """延迟导入主题资源，兼容测试桩环境。"""

    theme_module = import_module("ui.theme")
    ThemeManager = getattr(theme_module, "ThemeManager")
    builtin = getattr(theme_module, "BUILTIN_THEMES", None)
    if builtin is None:
        light_theme = getattr(theme_module, "workspace_light")
        dark_theme = getattr(theme_module, "workspace_dark")
        builtin = (light_theme, dark_theme)
    return ThemeManager, tuple(builtin)


class _HeadlessStatusBar:
    def showMessage(self, *_args, **_kwargs):
        return None


class ToolsetWindow(QtWidgets.QMainWindow):
    """包含主界面与控制器的窗口封装。"""

    def __init__(self):
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)

        ThemeManager, builtin_themes = _load_theme_resources()
        self.theme_manager = ThemeManager()
        self.theme_manager.register_many(builtin_themes)
        if builtin_themes:
            self.theme_manager.apply_theme(builtin_themes[0].name)

        self.controller = MainWindowController(self, self.ui, self.theme_manager)
        self._headless_controller: MainWindowController | None = None

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            controller = self._resolve_controller()
            if hasattr(controller, item):
                return getattr(controller, item)
            raise

    def perform_task(self, *args, **kwargs):
        controller = self._resolve_controller()
        return controller.perform_task(*args, **kwargs)

    def _resolve_controller(self) -> MainWindowController:
        try:
            controller = object.__getattribute__(self, "controller")
        except AttributeError:
            controller = None
        if controller is not None:
            return controller

        try:
            proxy = object.__getattribute__(self, "_headless_controller")
        except AttributeError:
            proxy = None
        if proxy is None:
            proxy = MainWindowController.__new__(MainWindowController)
            proxy.printf_queue = queue.Queue()
            proxy.status = _HeadlessStatusBar()
            proxy._preferences = configuration.get_preferences()
            proxy.time_zone = proxy._read_config_timezone()
            proxy.tr = lambda text, *_args, **_kwargs: text
            self._headless_controller = proxy
        return proxy


toolsetWindow = ToolsetWindow


def main() -> None:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = ToolsetWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
