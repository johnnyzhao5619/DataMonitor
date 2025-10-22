import datetime
import sys
import threading
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(
        RequestException=Exception,
        get=lambda *args, **kwargs: types.SimpleNamespace(status_code=200),
        post=lambda *args, **kwargs: types.SimpleNamespace(status_code=200),
    )

import pytest

import configuration  # noqa: E402  pylint: disable=wrong-import-position
import logRecorder  # noqa: E402  pylint: disable=wrong-import-position
from monitoring.service import (  # noqa: E402
    MonitorScheduler,
    MonitorStrategy,
    default_notification_templates,
)
from monitoring.state_machine import (  # noqa: E402
    MonitorState,
    MonitorStateMachine,
    NotificationTemplates,
)


@pytest.fixture(autouse=True)
def reset_template_manager():
    configuration.get_template_manager.cache_clear()
    yield
    configuration.get_template_manager.cache_clear()


class SequenceStrategy(MonitorStrategy):
    def __init__(self, results):
        self._results = iter(results)
        self._last = results[-1] if results else True

    def run(self, monitor):
        try:
            self._last = next(self._results)
        except StopIteration:
            pass
        return self._last


class PerMonitorSequenceStrategy(MonitorStrategy):
    def __init__(self, sequences, default=True):
        self._default = default
        self._iterators = {}
        self._last_values = {}
        for monitor, results in sequences.items():
            sequence = tuple(results)
            if sequence:
                self._iterators[monitor] = iter(sequence)
                self._last_values[monitor] = sequence[-1]
            else:
                self._iterators[monitor] = iter(())
                self._last_values[monitor] = default

    def run(self, monitor):
        iterator = self._iterators.get(monitor)
        if iterator is None:
            return self._default

        try:
            value = next(iterator)
        except StopIteration:
            return self._last_values.get(monitor, self._default)

        self._last_values[monitor] = value
        return value


def test_state_machine_transitions_and_notifications():
    monitor = configuration.MonitorItem(
        name="ServiceA",
        url="http://example.com",
        monitor_type="GET",
        interval=30,
        email="ops@example.com",
    )

    templates = NotificationTemplates(
        channel="email",
        build_outage=lambda name, ts: (f"Outage {name}", ts.isoformat()),
        build_recovery=lambda name, ts: (f"Recovery {name}", ts.isoformat()),
    )

    machine = MonitorStateMachine(monitor, templates)
    base_time = datetime.datetime(2023, 1, 1, 0, 0, 0)

    event1 = machine.transition(True, base_time, base_time)
    assert event1.status is MonitorState.HEALTHY
    assert event1.notification is None

    event2 = machine.transition(False, base_time, base_time)
    assert event2.status is MonitorState.OUTAGE
    assert event2.notification.subject.startswith("Outage")
    assert event2.notification.recipients == "ops@example.com"

    event3 = machine.transition(False, base_time, base_time)
    assert event3.status is MonitorState.OUTAGE_ONGOING
    assert event3.notification is None

    event4 = machine.transition(True, base_time, base_time)
    assert event4.status is MonitorState.RECOVERED
    assert event4.notification.subject.startswith("Recovery")


def test_state_machine_respects_template_overrides(tmp_path, monkeypatch):
    templates_content = """[ui]\nstatus_line = [{event_timestamp}] {service_name}::{status_label}\n[log]\naction_line = ACTION {service_name} {monitor_type}\ndetail_line = DETAIL {status_text} @ {event_timestamp}\n"""
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))
    config_dir = tmp_path / "Config"
    config_dir.mkdir(parents=True, exist_ok=True)
    template_path = config_dir / configuration.TEMPLATE_CONFIG_NAME
    template_path.write_text(templates_content, encoding="utf-8")

    monitor = configuration.MonitorItem(
        name="ServiceA",
        url="http://example.com",
        monitor_type="GET",
        interval=30,
        email="ops@example.com",
    )
    templates = NotificationTemplates(
        channel="email",
        build_outage=lambda name, ts: (f"Outage {name}", ts.isoformat()),
        build_recovery=lambda name, ts: (f"Recovery {name}", ts.isoformat()),
    )
    machine = MonitorStateMachine(monitor, templates)
    base_time = datetime.datetime(2023, 1, 1, 8, 30, 0)

    event = machine.transition(False, base_time, base_time)

    assert event.message == "[2023-01-01 08:30:00] ServiceA::服务异常"
    assert event.log_action == "ACTION ServiceA GET"
    assert event.log_detail == "DETAIL 异常 @ 2023-01-01 08:30:00"


def test_scheduler_runs_strategies_and_emits_events(monkeypatch):
    notifications = []
    logs = []
    csv_rows = []
    events = []
    finished = threading.Event()

    monkeypatch.setattr(logRecorder, "record", lambda action, detail: logs.append((action, detail)))
    monkeypatch.setattr(logRecorder, "saveToFile", lambda row, name: csv_rows.append((tuple(row), name)))

    base_time = datetime.datetime(2023, 1, 1, 0, 0, 0)

    def capture_event(event):
        events.append(event)
        if len(events) >= 4:
            finished.set()

    scheduler = MonitorScheduler(
        event_handler=capture_event,
        timezone_getter=lambda: 0,
        clock=lambda: base_time,
        templates=NotificationTemplates(
            channel="email",
            build_outage=lambda name, ts: (f"{name}-outage", ts.isoformat()),
            build_recovery=lambda name, ts: (f"{name}-recovery", ts.isoformat()),
        ),
        dispatcher=lambda notification: notifications.append(notification),
    )

    scheduler.register_strategy("GET", SequenceStrategy([True, False, False, True]))

    monitor = configuration.MonitorItem(
        name="ServiceA",
        url="http://example.com",
        monitor_type="GET",
        interval=0.1,
        email="ops@example.com",
    )

    scheduler.start([monitor])
    try:
        assert finished.wait(5), "调度器未在预期时间内产生事件"
    finally:
        scheduler.stop()

    assert len(events) >= 4
    statuses = [event.status for event in events[:4]]
    assert statuses == [
        MonitorState.HEALTHY,
        MonitorState.OUTAGE,
        MonitorState.OUTAGE_ONGOING,
        MonitorState.RECOVERED,
    ]


def test_scheduler_handles_payload_and_headers_monitor(monkeypatch):
    notifications = []
    logs = []
    csv_rows = []
    events = []
    finished = threading.Event()

    monkeypatch.setattr(logRecorder, "record", lambda action, detail: logs.append((action, detail)))
    monkeypatch.setattr(
        logRecorder,
        "saveToFile",
        lambda row, name: csv_rows.append((tuple(row), name)),
    )

    base_time = datetime.datetime(2023, 1, 1, 12, 0, 0)

    def capture_event(event):
        events.append(event)
        if len(events) >= 3:
            finished.set()

    scheduler = MonitorScheduler(
        event_handler=capture_event,
        timezone_getter=lambda: 0,
        clock=lambda: base_time,
        templates=NotificationTemplates(
            channel="email",
            build_outage=lambda name, ts: (f"{name}-outage", ts.isoformat()),
            build_recovery=lambda name, ts: (f"{name}-recovery", ts.isoformat()),
        ),
        dispatcher=lambda notification: notifications.append(notification),
    )

    scheduler.register_strategy("POST", SequenceStrategy([True, False, True]))

    monitor = configuration.MonitorItem(
        name="ServiceWithPayload",
        url="http://example.com/api",
        monitor_type="POST",
        interval=0.05,
        email="ops@example.com",
        payload={"query": "value"},
        headers={"Authorization": "Bearer token"},
    )

    scheduler.start([monitor])
    try:
        assert finished.wait(5), "调度器未在预期时间内处理带 payload 的监控"
    finally:
        scheduler.stop()

    assert len(events) >= 3
    statuses = [event.status for event in events[:3]]
    assert statuses == [
        MonitorState.HEALTHY,
        MonitorState.OUTAGE,
        MonitorState.RECOVERED,
    ]

    assert len(notifications) == 2
    assert notifications[0].subject.endswith("-outage")
    assert notifications[1].subject.endswith("-recovery")

    assert any("服务异常" in detail for _, detail in logs)
    assert any(row[0][6] in {"异常", "持续异常"} for row in csv_rows)


def test_default_notification_templates_builders():
    templates = default_notification_templates()
    occurred_at = datetime.datetime(2023, 1, 1, 12, 0, 0)

    subject, body = templates.build_outage("ServiceA", occurred_at)
    assert subject.strip()
    assert body.strip()

    subject, body = templates.build_recovery("ServiceA", occurred_at)
    assert subject.strip()
    assert body.strip()


def test_scheduler_uses_default_templates(monkeypatch):
    notifications = []
    events = []
    finished = threading.Event()

    monkeypatch.setattr(logRecorder, "record", lambda action, detail: None)
    monkeypatch.setattr(logRecorder, "saveToFile", lambda row, name: None)

    base_time = datetime.datetime(2023, 1, 1, 0, 0, 0)

    def capture_event(event):
        events.append(event)
        if len(events) >= 3:
            finished.set()

    scheduler = MonitorScheduler(
        event_handler=capture_event,
        timezone_getter=lambda: 0,
        clock=lambda: base_time,
        dispatcher=lambda notification: notifications.append(notification),
    )
    scheduler.register_strategy("GET", SequenceStrategy([True, False, True]))

    monitor = configuration.MonitorItem(
        name="ServiceA",
        url="http://example.com",
        monitor_type="GET",
        interval=0.1,
        email="ops@example.com",
    )

    scheduler.start([monitor])
    try:
        assert finished.wait(5), "调度器未在预期时间内产生事件"
    finally:
        scheduler.stop()

    assert len(notifications) == 2
    for notification in notifications:
        assert notification.subject.strip()
        assert notification.body.strip()


def test_scheduler_handles_monitors_with_same_name(monkeypatch):
    monkeypatch.setattr(logRecorder, "record", lambda action, detail: None)
    monkeypatch.setattr(logRecorder, "saveToFile", lambda row, name: None)

    base_time = datetime.datetime(2023, 1, 1, 0, 0, 0)

    monitor_primary = configuration.MonitorItem(
        name="Duplicate",
        url="http://example.com/api/one",
        monitor_type="GET",
        interval=0,
        email="ops@example.com",
    )
    monitor_secondary = configuration.MonitorItem(
        name="Duplicate",
        url="http://example.com/api/two",
        monitor_type="GET",
        interval=0,
        email="ops@example.com",
    )

    strategy = PerMonitorSequenceStrategy(
        {
            monitor_primary: [True, False, True],
            monitor_secondary: [True, False, False],
        }
    )

    events_by_monitor = {monitor_primary: [], monitor_secondary: []}
    notifications_by_monitor = {monitor_primary: [], monitor_secondary: []}
    expected_counts = {monitor_primary: 3, monitor_secondary: 3}
    finished = threading.Event()

    def capture_event(event):
        events = events_by_monitor.setdefault(event.monitor, [])
        events.append(event.status)
        if event.notification:
            notifications = notifications_by_monitor.setdefault(event.monitor, [])
            notifications.append(event.notification.subject)
        if all(
            len(events_by_monitor[monitor]) >= expected_counts[monitor]
            for monitor in expected_counts
        ):
            finished.set()

    scheduler = MonitorScheduler(
        event_handler=capture_event,
        timezone_getter=lambda: 0,
        clock=lambda: base_time,
        templates=NotificationTemplates(
            channel="email",
            build_outage=lambda name, ts: (f"{name}-outage", ts.isoformat()),
            build_recovery=lambda name, ts: (f"{name}-recovery", ts.isoformat()),
        ),
        dispatcher=lambda notification: None,
    )
    scheduler.register_strategy("GET", strategy)

    scheduler.start([monitor_primary, monitor_secondary])
    try:
        assert finished.wait(5), "调度器未在预期时间内产生事件"
    finally:
        scheduler.stop()

    assert events_by_monitor[monitor_primary][:3] == [
        MonitorState.HEALTHY,
        MonitorState.OUTAGE,
        MonitorState.RECOVERED,
    ]
    assert events_by_monitor[monitor_secondary][:3] == [
        MonitorState.HEALTHY,
        MonitorState.OUTAGE,
        MonitorState.OUTAGE_ONGOING,
    ]

    assert notifications_by_monitor[monitor_primary] == [
        "Duplicate-outage",
        "Duplicate-recovery",
    ]
    assert notifications_by_monitor[monitor_secondary] == ["Duplicate-outage"]
