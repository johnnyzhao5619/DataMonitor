import sys
from dataclasses import asdict
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration
import logRecorder
import sendEmail
import time

pytest.importorskip("PyQt5")
from PyQt5 import QtCore

from mainFrame import toolsetWindow
from ui.main_window import ConfigWizard


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
    saved = asdict(monitors[0])
    assert saved["name"] == "测试服务"
    assert saved["url"] == "http://example.com/api"
    assert saved["monitor_type"] == "GET"
    assert saved["interval"] == 120
    assert saved["email"] == "ops@example.com"

    assert window.ui.contentStack.currentIndex() == window.ui.monitor_view_index


@pytest.mark.qt
def test_config_wizard_loads_existing_monitor_items(qtbot):
    monitors = [
        configuration.MonitorItem(
            name="服务一",
            url="http://example.com/a",
            monitor_type="GET",
            interval=45,
            email="team@example.com",
            payload={"foo": "bar"},
            headers={"Accept": "application/json"},
        ),
        configuration.MonitorItem(
            name="服务二",
            url="http://example.com/b",
            monitor_type="POST",
            interval=120,
            email=None,
            payload=None,
            headers=None,
        ),
    ]

    wizard = ConfigWizard()
    qtbot.addWidget(wizard)
    wizard.show()

    wizard.load_monitors(monitors)

    assert wizard.monitorList.count() == 2
    assert wizard.monitorList.currentRow() == 0
    assert wizard.nameEdit.text() == "服务一"
    assert wizard.urlEdit.text() == "http://example.com/a"
    assert wizard.typeCombo.currentText() == "GET"
    assert wizard.intervalSpin.value() == 45
    assert wizard.emailEdit.text() == "team@example.com"

    loaded = wizard.get_monitors()
    assert len(loaded) == 2
    assert loaded[0]["payload"] == {"foo": "bar"}
    assert loaded[0]["headers"] == {"Accept": "application/json"}
    assert loaded[1]["type"] == "POST"
    assert loaded[1]["email"] == ""


@pytest.mark.qt
def test_run_periodically_single_iteration(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = toolsetWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        sendEmail,
        "render_email",
        lambda event, context: (f"subject-{event}", f"body-{event}"),
    )
    monkeypatch.setattr(sendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(configuration, "render_template", lambda *args, **kwargs: "mock")
    monkeypatch.setattr(logRecorder, "record", lambda *args, **kwargs: None)
    monkeypatch.setattr(logRecorder, "saveToFile", lambda *args, **kwargs: None)

    call_count = {"perform": 0}

    def fake_perform(*args, **kwargs):
        call_count["perform"] += 1
        return True

    window.perform_task = fake_perform

    def fake_sleep(interval):
        raise StopIteration

    monkeypatch.setattr(time, "sleep", fake_sleep)

    monitor_info = {
        "name": "测试服务",
        "url": "http://example.com",
        "type": "GET",
        "interval": 1,
        "email": "ops@example.com",
    }

    with pytest.raises(StopIteration):
        window.run_periodically(monitor_info)

    assert call_count["perform"] == 1
