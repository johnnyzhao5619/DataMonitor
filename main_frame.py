# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 11:53 p.m.
# @Author: John Zhao
"""Entry point window definition for the application."""

from importlib import import_module
from typing import TYPE_CHECKING

import configuration
from PySide6 import QtWidgets

from controllers import MainWindowController
from ui.main_window import MainWindowUI

if TYPE_CHECKING:
    from ui.theme import ThemeDefinition, ThemeManager


def _load_theme_resources(
) -> tuple["ThemeManager", tuple["ThemeDefinition", ...]]:
    """Lazily import theme resources so they work in stubbed test environments."""

    theme_module = import_module("ui.theme")
    ThemeManager = getattr(theme_module, "ThemeManager")
    builtin = getattr(theme_module, "BUILTIN_THEMES", None)
    if builtin is None:
        light_theme = getattr(theme_module, "workspace_light")
        dark_theme = getattr(theme_module, "workspace_dark")
        builtin = (light_theme, dark_theme)
    return ThemeManager, tuple(builtin)


class ToolsetWindow(QtWidgets.QMainWindow):
    """Window wrapper that bundles the main UI and its controller."""

    def __init__(self):
        super().__init__()
        configuration.configure_logging()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)

        ThemeManager, builtin_themes = _load_theme_resources()
        self.theme_manager = ThemeManager()
        self.theme_manager.register_many(builtin_themes)
        if builtin_themes:
            self.theme_manager.apply_theme(builtin_themes[0].name)

        self.controller = MainWindowController(self, self.ui,
                                               self.theme_manager)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            controller = getattr(self, "controller", None)
            if controller is not None and hasattr(controller, item):
                return getattr(controller, item)
            raise


toolsetWindow = ToolsetWindow


def main() -> None:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = ToolsetWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
