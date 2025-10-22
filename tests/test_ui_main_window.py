import pytest

pytest.importorskip("PyQt5")
from PyQt5 import QtCore

import configuration
from mainFrame import toolsetWindow


@pytest.mark.qt
def test_configuration_wizard_round_trip(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = toolsetWindow()
    qtbot.addWidget(window)
    window.show()
    window.show_configuration()

    wizard = window.ui.configWizard
    assert wizard.monitorList.count() == 0

    qtbot.mouseClick(wizard.addButton, QtCore.Qt.LeftButton)
    assert wizard.monitorList.count() == 1

    wizard.nameEdit.setText("测试服务")
    wizard.urlEdit.setText("http://example.com/api")
    wizard.typeCombo.setCurrentText("GET")
    wizard.intervalSpin.setValue(120)
    wizard.emailEdit.setText("ops@example.com")

    assert wizard.saveButton.isEnabled()

    qtbot.mouseClick(wizard.saveButton, QtCore.Qt.LeftButton)

    monitors = configuration.read_monitor_list()
    assert len(monitors) == 1
    saved = monitors[0]
    assert saved["name"] == "测试服务"
    assert saved["url"] == "http://example.com/api"
    assert saved["type"] == "GET"
    assert saved["interval"] == 120
    assert saved["email"] == "ops@example.com"

    assert window.ui.contentStack.currentIndex() == window.ui.monitor_view_index
