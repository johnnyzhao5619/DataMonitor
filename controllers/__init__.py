"""Collection of controller modules."""

from PySide6 import QtCore


class ControllerEventBus(QtCore.QObject):
    """Unified event bus for cross-controller communication."""

    logMessage = QtCore.Signal(str)
    statusMessage = QtCore.Signal(str, int)
    monitoringToggled = QtCore.Signal(bool)
    timezoneChanged = QtCore.Signal(int)
    languageChanged = QtCore.Signal(str)
    themeChanged = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)


from .dashboard import DashboardController
from .main_window import MainWindowController
from .preferences import PreferencesController


__all__ = [
    "ControllerEventBus",
    "DashboardController",
    "MainWindowController",
    "PreferencesController",
]
