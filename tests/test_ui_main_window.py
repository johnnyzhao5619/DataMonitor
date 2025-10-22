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
import threading

pytest.importorskip("PyQt5")
from PyQt5 import QtCore

import apiMonitor

from mainFrame import toolsetWindow
from monitoring.service import parse_network_address as service_parse_network_address
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
@pytest.mark.parametrize(
    "monitor_type,url",
    [
        ("GET", "http://example.com"),
        ("SERVER", "https://example.com:8443/status"),
    ],
)
def test_run_periodically_single_iteration(qtbot, tmp_path, monkeypatch, monitor_type, url):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = toolsetWindow()
    qtbot.addWidget(window)

    send_calls = []

    def fake_send_email(*args, **kwargs):
        send_calls.append((args, kwargs))

    monkeypatch.setattr(sendEmail, "send_email", fake_send_email)

    def fake_render_template(category, key, context):
        return f"{category}.{key}|{context['service_name']}|{context['status_text']}"

    monkeypatch.setattr(configuration, "render_template", fake_render_template)

    recorded_logs = []

    def fake_record(action, detail):
        recorded_logs.append((action, detail))

    monkeypatch.setattr(logRecorder, "record", fake_record)

    saved_rows = []

    def fake_save(data, name):
        saved_rows.append((data, name))

    monkeypatch.setattr(logRecorder, "saveToFile", fake_save)

    call_count = {"perform": 0}

    def fake_sleep(interval):
        raise StopIteration

    monkeypatch.setattr(time, "sleep", fake_sleep)

    expected_parsed = None
    if monitor_type == "SERVER":
        expected_parsed = service_parse_network_address(url)

    def fake_perform(url_arg, parsed_address, monitor_type_arg, *args, **kwargs):
        call_count["perform"] += 1
        assert monitor_type_arg == monitor_type
        if monitor_type == "SERVER":
            assert parsed_address == expected_parsed
        else:
            assert parsed_address is None
        return True

    window.perform_task = fake_perform

    monitor_info = {
        "name": "测试服务",
        "url": url,
        "type": monitor_type,
        "interval": 1,
        "email": "ops@example.com",
    }
    with pytest.raises(StopIteration):
        window.run_periodically(monitor_info)

    assert send_calls == []
    assert recorded_logs == [
        (
            "log.action_line|测试服务|正常",
            "log.detail_line|测试服务|正常",
        )
    ]
    assert saved_rows and saved_rows[0][1] == "测试服务"
    row = list(saved_rows[0][0])
    assert row[1] == "测试服务"
    assert row[2] == monitor_type
    assert row[5] == 1
    assert row[6] == "正常"
    assert window.printf_queue.get_nowait() == "ui.status_line|测试服务|正常"

    qtbot.waitUntil(lambda: len(thread_names) >= 2, timeout=3000)
    assert all(name.startswith("Monitor:") for name in thread_names)

    timer = window._periodic_timers[monitor_info["name"]]
    assert timer.isActive()

    window._stop_periodic_monitors()
