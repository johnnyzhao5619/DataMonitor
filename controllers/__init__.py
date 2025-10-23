"""控制器模块集合。"""

from PyQt5 import QtCore

from .dashboard import DashboardController
from .main_window import MainWindowController
from .preferences import PreferencesController


class ControllerEventBus(QtCore.QObject):
    """跨控制器通信的统一事件总线。"""

    logMessage = QtCore.pyqtSignal(str)
    statusMessage = QtCore.pyqtSignal(str, int)
    monitoringToggled = QtCore.pyqtSignal(bool)
    timezoneChanged = QtCore.pyqtSignal(int)
    languageChanged = QtCore.pyqtSignal(str)
    themeChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)


__all__ = [
    "ControllerEventBus",
    "DashboardController",
    "MainWindowController",
    "PreferencesController",
]
