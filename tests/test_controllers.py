import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytest.importorskip("PyQt5")
from PyQt5 import QtWidgets

import configuration
from monitoring import log_recorder
from controllers import ControllerEventBus
from controllers.dashboard import DashboardController
from controllers.preferences import PreferencesController
from main_frame import _load_theme_resources
from ui.main_window import MainWindowUI


class DummyScheduler:
    def __init__(self, *, event_handler=None, timezone_getter=None):
        self.event_handler = event_handler
        self.timezone_getter = timezone_getter
        self.started = False
        self.monitors = []
        self.prune_calls = []

    def start(self, monitors):
        self.started = True
        self.monitors = list(monitors)

    def stop(self):
        self.started = False

    def run_single_cycle(self, monitor):
        event = types.SimpleNamespace(
            monitor=monitor,
            message=f"cycle:{monitor.name}",
            status_bar_message=self.started and "status" or "",
        )
        if self.event_handler:
            self.event_handler(event)
        return event

    def register_strategy(self, *_args, **_kwargs):
        return None

    def prune_state_machines(self, monitors):
        self.prune_calls.append(tuple(monitors))


@pytest.mark.qt
def test_dashboard_start_and_stop_emits_signals(qtbot, monkeypatch):
    monitor = configuration.MonitorItem(
        name="服务A",
        url="http://example.com",
        monitor_type="GET",
        interval=30,
        email=None,
    )
    monkeypatch.setattr(configuration, "read_monitor_list", lambda: [monitor])
    monkeypatch.setattr("controllers.dashboard.MonitorScheduler", DummyScheduler)

    bus = ControllerEventBus()
    log_messages = []
    status_messages = []
    toggled = []
    bus.logMessage.connect(log_messages.append)
    bus.statusMessage.connect(lambda text, timeout: status_messages.append((text, timeout)))
    bus.monitoringToggled.connect(toggled.append)

    controller = DashboardController(event_bus=bus, timezone=8)
    qtbot.addCleanup(controller.on_close)

    assert controller.start_monitoring() is True
    assert controller.is_running
    assert toggled == [True]
    assert any("目前读取到" in msg for msg in log_messages)
    assert any(msg.endswith("服务A") or "服务A" in msg for msg in log_messages)
    assert any("监控已启动" in msg for msg, _ in status_messages)

    controller.stop_monitoring()
    assert toggled[-1] is False
    assert not controller.is_running
    assert any("监控已停止" in msg for msg, _ in status_messages)


@pytest.mark.qt
def test_dashboard_run_periodically_triggers_event(qtbot, monkeypatch):
    monkeypatch.setattr("controllers.dashboard.MonitorScheduler", DummyScheduler)
    bus = ControllerEventBus()
    captured = []
    bus.logMessage.connect(captured.append)

    controller = DashboardController(event_bus=bus, timezone=0)
    qtbot.addCleanup(controller.on_close)

    monitor_info = {
        "name": "周期服务",
        "url": "http://example.com/health",
        "type": "GET",
        "interval": 1,
    }

    controller.run_periodically(monitor_info)
    qtbot.waitUntil(lambda: any(msg.startswith("cycle:") for msg in captured), timeout=2000)
    assert any("周期服务" in msg for msg in captured)
    prune_calls = controller._periodic_scheduler.prune_calls
    assert prune_calls and len(prune_calls[-1]) == 1


@pytest.mark.qt
def test_dashboard_logs_unsupported_type(monkeypatch, qtbot):
    monkeypatch.setattr("controllers.dashboard.MonitorScheduler", DummyScheduler)
    logged = []
    statuses = []
    bus = ControllerEventBus()
    bus.logMessage.connect(logged.append)
    bus.statusMessage.connect(lambda text, timeout: statuses.append(text))

    records = []
    monkeypatch.setattr(log_recorder, "record", lambda action, detail: records.append((action, detail)))

    controller = DashboardController(event_bus=bus, timezone=0)
    qtbot.addCleanup(controller.on_close)

    controller.run_periodically(
        {
            "name": "异常服务",
            "url": "http://example.com",
            "type": "UNKNOWN",
            "interval": 1,
        }
    )

    assert records and records[0][0] == "Unsupported Monitor Type"
    assert any("未被支持" in message for message in logged)
    assert any("异常服务" in message for message in statuses)


@pytest.mark.qt
def test_preferences_language_and_timezone_persistence(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("APIMONITOR_HOME", str(tmp_path))
    config_dir = tmp_path / "Config"
    configuration.writeconfig(str(config_dir))
    configuration.write_monitor_list([])

    window = QtWidgets.QMainWindow()
    qtbot.addWidget(window)
    ui = MainWindowUI()
    ui.setup_ui(window)

    ThemeManager, builtin = _load_theme_resources()
    theme_manager = ThemeManager()
    theme_manager.register_many(builtin)
    if builtin:
        theme_manager.apply_theme(builtin[0].name)

    bus = ControllerEventBus()
    language_events = []
    status_messages = []
    timezone_events = []
    bus.languageChanged.connect(language_events.append)
    bus.statusMessage.connect(lambda text, timeout: status_messages.append(text))
    bus.timezoneChanged.connect(timezone_events.append)

    preferences = PreferencesController(
        window=window,
        ui=ui,
        theme_manager=theme_manager,
        event_bus=bus,
    )
    qtbot.addCleanup(preferences.on_close)

    preferences.setup()
    assert language_events
    assert timezone_events
    assert language_events[-1] == preferences.current_language
    assert timezone_events[-1] == preferences.current_timezone

    selector = ui.languageSelector
    en_index = selector.findData("en_US")
    assert en_index >= 0
    preferences.on_language_changed(en_index)
    qtbot.waitUntil(lambda: preferences.current_language == "en_US", timeout=2000)
    assert any("语言" in message for message in status_messages)
    config_file = config_dir / "Config.ini"
    assert "language = en_US" in config_file.read_text(encoding="utf-8")

    monkeypatch.setattr(QtWidgets.QInputDialog, "getInt", lambda *args, **kwargs: (9, True))
    preferences.choose_timezone()
    qtbot.waitUntil(lambda: preferences.current_timezone == 9, timeout=2000)
    assert any("UTC+9" in message for message in status_messages)
    assert "timezone = 9" in config_file.read_text(encoding="utf-8")

    theme_selector = ui.themeSelector
    if theme_selector.count() > 1:
        next_index = (theme_selector.currentIndex() + 1) % theme_selector.count()
        preferences.on_theme_changed(next_index)
        assert any("主题" in message for message in status_messages)
