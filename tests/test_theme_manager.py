import json

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration

pytest.importorskip("PySide6")
from PySide6 import QtWidgets

from ui.theme import ThemeManager, workspace_dark, workspace_light


@pytest.mark.qt
def test_theme_manager_registers_external_definitions(tmp_path, monkeypatch, qtbot):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    theme_dir = tmp_path / "Config" / ThemeManager.THEME_CONFIG_DIRNAME
    theme_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "name": "custom_light",
        "display_name": "Custom Light",
        "descriptions": {
            "zh_CN": "自定义浅色主题",
            "en_US": "Custom light theme",
        },
        "tokens": {
            "colors": {
                "accent": "#FF3366",
                "accent_hover": "#FF6688",
            }
        },
    }
    (theme_dir / "custom.json").write_text(json.dumps(payload), encoding="utf-8")

    _ = qtbot  # ensure QApplication fixture is active
    app = QtWidgets.QApplication.instance()
    assert app is not None
    manager = ThemeManager(app)
    manager.register_many((workspace_light, workspace_dark))

    names = manager.available_themes()
    assert names[0] == "workspace_light"
    assert "custom_light" in names

    theme = manager.get_theme("custom_light")
    assert theme.tokens.colors.accent == "#FF3366"
    assert theme.metadata.display_name == "Custom Light"
    assert theme.metadata.description_for("zh_CN") == "自定义浅色主题"
    assert theme.metadata.is_high_contrast is False
    stylesheet = theme.build_stylesheet()
    assert "#FF3366" in stylesheet
