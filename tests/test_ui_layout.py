from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytest.importorskip("PyQt5")
from PyQt5 import QtCore

from main_frame import toolsetWindow
from ui.views.configuration import ConfigWizard
from ui.views.dashboard import MonitorDashboard


@pytest.mark.qt
def test_main_window_layout_structure(qtbot):
    window = toolsetWindow()
    qtbot.addWidget(window)

    ui = window.ui
    assert ui.commandBar.objectName() == "commandBar"
    assert ui.toggleMonitoringButton.objectName() == "toggleMonitoringButton"
    assert ui.reloadConfigButton.objectName() == "reloadConfigButton"
    assert ui.current_status_text() == ui.tr("Standby")

    assert ui.navigationBar.active_id() == "monitor"

    assert ui.contentStack.count() == 4
    assert ui.monitor_view_index == 0
    assert ui.config_view_index == 1
    assert ui.preferences_view_index == 2
    assert ui.report_view_index == 3

    assert isinstance(ui.contentStack.widget(ui.monitor_view_index), MonitorDashboard)
    assert isinstance(ui.configWizard, ConfigWizard)
    assert ui.contentStack.widget(ui.config_view_index).objectName() == "configurationWorkspace"
    assert ui.contentStack.widget(ui.preferences_view_index).objectName() == "preferencesPage"
    assert ui.contentStack.widget(ui.report_view_index).objectName() == "reportsPlaceholder"

    assert ui.reportPlaceholderLabel.objectName() == "reportsPlaceholderLabel"
    assert ui.timezoneDisplay.objectName() == "timezoneDisplay"


@pytest.mark.qt
def test_navigation_updates_stack_and_highlight(qtbot):
    window = toolsetWindow()
    qtbot.addWidget(window)

    received = []
    window.ui.navigationRequested.connect(received.append)

    qtbot.mouseClick(window.ui.navigationBar.configButton, QtCore.Qt.LeftButton)
    assert received and received[-1] == "configuration"
    assert window.ui.contentStack.currentIndex() == window.ui.config_view_index
    assert window.ui.navigationBar.active_id() == "configuration"

    qtbot.mouseClick(window.ui.navigationBar.preferencesButton, QtCore.Qt.LeftButton)
    assert received and received[-1] == "preferences"
    assert window.ui.contentStack.currentIndex() == window.ui.preferences_view_index
    assert window.ui.navigationBar.active_id() == "preferences"

    qtbot.mouseClick(window.ui.navigationBar.reportButton, QtCore.Qt.LeftButton)
    assert received and received[-1] == "reports"
    assert window.ui.contentStack.currentIndex() == window.ui.report_view_index
    assert window.ui.navigationBar.active_id() == "reports"

    qtbot.mouseClick(window.ui.navigationBar.monitorButton, QtCore.Qt.LeftButton)
    assert received and received[-1] == "monitor"
    assert window.ui.contentStack.currentIndex() == window.ui.monitor_view_index
    assert window.ui.navigationBar.active_id() == "monitor"

    assert window.controller._navigation_shortcuts
