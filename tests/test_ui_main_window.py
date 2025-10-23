import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration
from monitoring import api_monitor, log_recorder, send_email
import threading

pytest.importorskip("PyQt5")
from PyQt5 import QtCore, QtWidgets

from main_frame import MainWindowController, toolsetWindow
from monitoring.service import parse_network_address as service_parse_network_address
from ui.components.navigation import NavigationBar
from ui.views.configuration import ConfigWizard

import controllers.main_window as main_window_module


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
def test_config_wizard_requires_hostname_before_save(qtbot):
    wizard = ConfigWizard()
    qtbot.addWidget(wizard)
    wizard.show()

    qtbot.mouseClick(wizard.addButton, QtCore.Qt.LeftButton)
    QtWidgets.QApplication.processEvents()

    assert wizard.urlEdit.text() == ""
    assert wizard.saveButton.isEnabled() is False
    assert "URL" in wizard.validationLabel.text()


@pytest.mark.qt
def test_config_wizard_accepts_valid_hostname(qtbot):
    wizard = ConfigWizard()
    qtbot.addWidget(wizard)
    wizard.show()

    qtbot.mouseClick(wizard.addButton, QtCore.Qt.LeftButton)
    wizard.urlEdit.setText("https://example.com/service")
    qtbot.waitUntil(lambda: wizard.saveButton.isEnabled(), timeout=1000)

    assert wizard.validationLabel.text() == ""


@pytest.mark.qt
def test_toggle_stop_only_halts_monitoring(qtbot, monkeypatch):
    window = toolsetWindow()
    qtbot.addWidget(window)

    class DummyScheduler:
        def __init__(self) -> None:
            self.stopped = False

        def stop(self) -> None:
            self.stopped = True

    dummy_scheduler = DummyScheduler()
    window.dashboard._scheduler = dummy_scheduler

    quit_calls = {"count": 0}

    def track_quit() -> None:
        quit_calls["count"] += 1

    monkeypatch.setattr(
        main_window_module.QtWidgets.QApplication,
        "quit",
        staticmethod(track_quit),
        raising=False,
    )

    window._on_toggle_monitoring()
    QtWidgets.QApplication.processEvents()

    assert dummy_scheduler.stopped is True
    assert window.dashboard._scheduler is None
    qtbot.waitUntil(lambda: "启动" in window.ui.toggleMonitoringButton.text(), timeout=1000)
    assert "待命" in window.ui.runStatusIndicator.text()
    assert quit_calls["count"] == 0


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

    monkeypatch.setattr(send_email, "send_email", fake_send_email)

    def fake_render_template(category, key, context, *, language=None):
        return f"{category}.{key}|{context['service_name']}|{context['status_text']}"

    monkeypatch.setattr(configuration, "render_template", fake_render_template)

    recorded_logs = []

    def fake_record(action, detail):
        recorded_logs.append((action, detail))

    monkeypatch.setattr(log_recorder, "record", fake_record)

    saved_rows = []

    def fake_save(data, name):
        saved_rows.append((data, name))

    monkeypatch.setattr(log_recorder, "saveToFile", fake_save)

    call_count = {"perform": 0}

    def fake_monitor_get(actual_url, timeout=None):
        assert monitor_type == "GET"
        assert actual_url == url
        call_count["perform"] += 1
        return True

    def fake_monitor_post(actual_url, payload=None, *, headers=None, timeout=None):
        assert monitor_type == "POST"
        assert actual_url == url
        call_count["perform"] += 1
        return True

    def fake_monitor_server(parsed_address, timeout=None):
        assert monitor_type == "SERVER"
        call_count["perform"] += 1
        assert parsed_address == expected_parsed
        return True

    monkeypatch.setattr(api_monitor, "monitor_get", fake_monitor_get)
    monkeypatch.setattr(api_monitor, "monitor_post", fake_monitor_post)
    monkeypatch.setattr(api_monitor, "monitor_server", fake_monitor_server)

    expected_parsed = None
    if monitor_type == "SERVER":
        expected_parsed = service_parse_network_address(url)

    thread_names = []

    original_thread = threading.Thread

    def tracking_thread(*args, **kwargs):
        name = kwargs.get("name")
        if name is None and len(args) >= 3:
            name = args[2]
        thread_names.append(name)
        return original_thread(*args, **kwargs)

    monkeypatch.setattr(threading, "Thread", tracking_thread)

    monitor_info = {
        "name": "测试服务",
        "url": url,
        "type": monitor_type,
        "interval": 1,
        "email": "ops@example.com",
    }

    window.controller.run_periodically(monitor_info)

    qtbot.waitUntil(lambda: len(recorded_logs) == 1, timeout=2000)
    qtbot.waitUntil(lambda: len(saved_rows) == 1, timeout=2000)
    qtbot.waitUntil(
        lambda: "ui.status_line|测试服务|正常" in window.ui.monitorBrowser.toPlainText(),
        timeout=2000,
    )
    qtbot.waitUntil(
        lambda: not window.controller.dashboard._running_periodic,
        timeout=2000,
    )

    assert send_calls == []
    assert call_count["perform"] == 1
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
    assert "ui.status_line|测试服务|正常" in window.ui.monitorBrowser.toPlainText()

    assert thread_names
    assert any(name and name.startswith("Monitor:") for name in thread_names)

    window.controller.dashboard.on_close()


@pytest.mark.qt
def test_run_periodically_with_duplicate_names(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = toolsetWindow()
    qtbot.addWidget(window)

    run_calls = []

    def fake_run_single_cycle(monitor):
        run_calls.append((monitor.name, monitor.url, monitor.monitor_type))

    monkeypatch.setattr(
        window.controller.dashboard._periodic_scheduler,
        "run_single_cycle",
        fake_run_single_cycle,
    )

    created_threads = []

    class ImmediateThread:
        def __init__(
            self,
            group=None,
            target=None,
            name=None,
            args=(),
            kwargs=None,
            daemon=None,
        ):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}
            self.name = name or "Thread"
            created_threads.append(self.name)

        def start(self):
            if self._target:
                self._target(*self._args, **self._kwargs)

    monkeypatch.setattr(threading, "Thread", ImmediateThread)

    monitors = [
        {
            "name": "重复服务",
            "url": "http://example.com/a",
            "type": "GET",
            "interval": 1,
        },
        {
            "name": "重复服务",
            "url": "http://example.com/b",
            "type": "GET",
            "interval": 1,
        },
    ]

    for info in monitors:
        window.controller.run_periodically(info)

    assert len(window.controller.dashboard._periodic_monitors) == 2
    assert len(window.controller.dashboard._periodic_timers) == 2
    assert created_threads == ["Monitor:重复服务", "Monitor:重复服务"]
    assert run_calls == [
        ("重复服务", "http://example.com/a", "GET"),
        ("重复服务", "http://example.com/b", "GET"),
    ]

    expected_keys = {
        ("重复服务", "http://example.com/a", "GET"),
        ("重复服务", "http://example.com/b", "GET"),
    }
    assert set(window.controller.dashboard._periodic_monitors.keys()) == expected_keys
    assert set(window.controller.dashboard._periodic_timers.keys()) == expected_keys
    urls = {monitor.url for monitor in window.controller.dashboard._periodic_monitors.values()}
    assert urls == {"http://example.com/a", "http://example.com/b"}
    assert window.controller.dashboard._running_periodic == set()

    window.controller.dashboard.on_close()


@pytest.mark.qt
def test_main_window_uses_navigation_bar(qtbot):
    window = toolsetWindow()
    qtbot.addWidget(window)

    assert isinstance(window.controller, MainWindowController)
    assert isinstance(window.ui.navigationBar, NavigationBar)
    assert isinstance(window.ui.toggleMonitoringButton, QtWidgets.QPushButton)
    assert isinstance(window.ui.reloadConfigButton, QtWidgets.QPushButton)
    assert window.ui.navigationBar.monitorButton.isCheckable()
    assert window.ui.navigationBar.configButton.isCheckable()
    assert window.ui.navigationBar.reportButton.isCheckable()
    assert window.ui.navigationBar.monitorButton.isChecked()

    theme_selector = window.ui.themeSelector
    assert theme_selector.count() >= 2
    current_theme_name = window.controller.theme_manager.current_theme_name()
    assert theme_selector.itemData(theme_selector.currentIndex()) == current_theme_name
    language_selector = window.ui.languageSelector
    assert isinstance(language_selector, QtWidgets.QComboBox)
    assert isinstance(window.ui.locationButton, QtWidgets.QPushButton)

    window.controller.show_configuration()
    assert window.ui.navigationBar.configButton.isChecked()
    assert not window.ui.navigationBar.monitorButton.isChecked()

    window.controller.show_reports()
    assert window.ui.navigationBar.reportButton.isChecked()


@pytest.mark.qt
def test_language_switch_updates_ui_and_templates(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = toolsetWindow()
    qtbot.addWidget(window)

    wizard = window.ui.configWizard
    assert wizard.addButton.text() == "新增"
    language_selector = window.ui.languageSelector
    en_index = language_selector.findData("en_US")
    assert en_index >= 0

    language_selector.setCurrentIndex(en_index)
    qtbot.waitUntil(lambda: window.controller._current_language == "en_US", timeout=2000)

    assert wizard.addButton.text() == "Add"
    assert window.ui.languageLabel.text().startswith("Language")
    assert window.ui.navigationBar.monitorButton.text() == "Monitor"

    context = {
        "service_name": "Example",
        "monitor_type": "GET",
        "url": "http://example.com",
        "interval": 30,
    }
    rendered = configuration.render_template("log", "action_line", context)
    assert "Type:" in rendered
    assert "类型" not in rendered

    zh_index = language_selector.findData("zh_CN")
    if zh_index >= 0:
        language_selector.setCurrentIndex(zh_index)
        qtbot.waitUntil(lambda: window.controller._current_language == "zh_CN", timeout=2000)

