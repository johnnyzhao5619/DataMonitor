"""用户界面模块。"""

from .components.navigation import NavigationBar
from .main_window import MainWindowUI
from .theme import (
    BUILTIN_THEMES,
    ThemeDefinition,
    ThemeManager,
    workspace_dark,
    workspace_high_contrast,
    workspace_light,
)
from .views.configuration import ConfigWizard

__all__ = [
    "MainWindowUI",
    "ConfigWizard",
    "NavigationBar",
    "ThemeDefinition",
    "ThemeManager",
    "workspace_light",
    "workspace_dark",
    "workspace_high_contrast",
    "BUILTIN_THEMES",
]
