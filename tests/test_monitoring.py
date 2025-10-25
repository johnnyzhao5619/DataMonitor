import datetime
import logging
import sys
import threading
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "requests" not in sys.modules:
    class _RequestException(Exception):
        """Minimal stand-in for ``requests.RequestException`` used in tests."""

    class _Timeout(_RequestException):
        """Minimal stand-in for ``requests.Timeout`` used in tests."""

    class _ConnectionError(_RequestException):
        """Minimal stand-in for ``requests.ConnectionError`` used in tests."""

    sys.modules["requests"] = types.SimpleNamespace(
        RequestException=_RequestException,
        Timeout=_Timeout,
        ConnectionError=_ConnectionError,
        get=lambda *args, **kwargs: types.SimpleNamespace(status_code=200),
        post=lambda *args, **kwargs: types.SimpleNamespace(status_code=200),
    )

import pytest

import configuration  # noqa: E402  pylint: disable=wrong-import-position
from monitoring import log_recorder  # noqa: E402  pylint: disable=wrong-import-position
from monitoring.service import (  # noqa: E402
    MonitorScheduler,
    MonitorStrategy,
    ServerMonitorStrategy,
    default_notification_templates,
    parse_network_address,
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
        build_outage=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
            f"Outage {name}",
            ts.isoformat(),
        ),
        build_recovery=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
            f"Recovery {name}",
            ts.isoformat(),
        ),
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
    configuration._LANGUAGE_CACHE = None
    configuration.set_language(configuration.DEFAULT_LANGUAGE)
    configuration.get_template_manager().reload()

    monitor = configuration.MonitorItem(
        name="ServiceA",
        url="http://example.com",
        monitor_type="GET",
        interval=30,
        email="ops@example.com",
    )
    templates = NotificationTemplates(
        channel="email",
        build_outage=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
            f"Outage {name}",
            ts.isoformat(),
        ),
        build_recovery=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
            f"Recovery {name}",
            ts.isoformat(),
        ),
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

    monkeypatch.setattr(log_recorder, "record", lambda action, detail: logs.append((action, detail)))
    monkeypatch.setattr(log_recorder, "saveToFile", lambda row, name: csv_rows.append((tuple(row), name)))

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
            build_outage=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-outage",
                ts.isoformat(),
            ),
            build_recovery=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-recovery",
                ts.isoformat(),
            ),
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


def test_parse_network_address_variants():
    assert parse_network_address("example.com") == ("http", "example.com", None, "")
    assert parse_network_address("https://example.org:8443/status") == (
        "https",
        "example.org",
        8443,
        "status",
    )
    assert parse_network_address("http://example.net/api/v1") == (
        "http",
        "example.net",
        None,
        "api/v1",
    )
    assert parse_network_address("https://[2001:db8::1]:8443/status/health") == (
        "https",
        "2001:db8::1",
        8443,
        "status/health",
    )
    assert parse_network_address("[2001:db8::2]/metrics") == (
        "http",
        "2001:db8::2",
        None,
        "metrics",
    )


def test_server_strategy_uses_shared_parser(monkeypatch):
    strategy = ServerMonitorStrategy()
    monitor = configuration.MonitorItem(
        name="ServerA",
        url="https://example.com:9443/health",
        monitor_type="SERVER",
        interval=30,
        email=None,
    )

    parse_calls = []

    def fake_parse(address):
        parse_calls.append(address)
        return ("https", "example.com", 9443, "health")

    monitor_calls = []

    monkeypatch.setattr("monitoring.service.parse_network_address", fake_parse)
    monkeypatch.setattr(
        "monitoring.service.api_monitor.monitor_server",
        lambda parsed: monitor_calls.append(parsed) or True,
    )

    assert strategy.run(monitor) is True
    assert strategy.run(monitor) is True

    assert parse_calls == ["https://example.com:9443/health"]
    assert monitor_calls == [("https", "example.com", 9443, "health"), ("https", "example.com", 9443, "health")]


def test_scheduler_handles_payload_and_headers_monitor(monkeypatch):
    notifications = []
    logs = []
    csv_rows = []
    events = []
    finished = threading.Event()

    monkeypatch.setattr(log_recorder, "record", lambda action, detail: logs.append((action, detail)))
    monkeypatch.setattr(
        log_recorder,
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
            build_outage=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-outage",
                ts.isoformat(),
            ),
            build_recovery=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-recovery",
                ts.isoformat(),
            ),
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

    monkeypatch.setattr(log_recorder, "record", lambda action, detail: None)
    monkeypatch.setattr(log_recorder, "saveToFile", lambda row, name: None)

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
    monkeypatch.setattr(log_recorder, "record", lambda action, detail: None)
    monkeypatch.setattr(log_recorder, "saveToFile", lambda row, name: None)

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
            build_outage=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-outage",
                ts.isoformat(),
            ),
            build_recovery=lambda name, ts, language=None: (  # noqa: ARG005 - 测试桩
                f"{name}-recovery",
                ts.isoformat(),
            ),
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


def test_scheduler_restart_after_stop(monkeypatch):
    monkeypatch.setattr(log_recorder, "record", lambda action, detail: None)
    monkeypatch.setattr(log_recorder, "saveToFile", lambda row, name: None)

    monitor = configuration.MonitorItem(
        name="Restartable",
        url="http://example.com/api",
        monitor_type="GET",
        interval=0,
        email=None,
    )

    scheduler = MonitorScheduler(event_handler=lambda event: None, timezone_getter=lambda: 0)
    scheduler.register_strategy("GET", SequenceStrategy([True]))

    scheduler.start([monitor])
    with pytest.raises(RuntimeError):
        scheduler.start([monitor])
    scheduler.stop()
    scheduler.start([monitor])
    scheduler.stop()


def test_scheduler_logs_strategy_exception(caplog):
    monitor = configuration.MonitorItem(
        name="ServiceWithError",
        url="http://example.com",
        monitor_type="GET",
        interval=60,
        email="ops@example.com",
    )

    class FailingStrategy(MonitorStrategy):
        def run(self, monitor):
            raise RuntimeError("boom")

    scheduler = MonitorScheduler(
        timezone_getter=lambda: 0,
        clock=lambda: datetime.datetime(2023, 1, 1, 0, 0, 0),
    )

    with caplog.at_level(logging.ERROR, logger="monitoring.service"):
        event = scheduler.run_single_cycle(monitor, strategy=FailingStrategy())

    assert event.monitor is monitor
    assert any(
        "monitor.scheduler.strategy_error" in record.message
        and monitor.name in record.message
        for record in caplog.records
    )


def test_scheduler_logs_event_handler_exception(caplog):
    monitor = configuration.MonitorItem(
        name="ServiceCallback",
        url="http://example.com",
        monitor_type="GET",
        interval=60,
        email="ops@example.com",
    )

    def failing_handler(event):
        raise RuntimeError("handler failed")

    scheduler = MonitorScheduler(
        event_handler=failing_handler,
        timezone_getter=lambda: 0,
        clock=lambda: datetime.datetime(2023, 1, 1, 0, 0, 0),
    )

    with caplog.at_level(logging.ERROR, logger="monitoring.service"):
        scheduler.run_single_cycle(monitor, strategy=SequenceStrategy([True]))

    assert any(
        "monitor.scheduler.event_handler_error" in record.message
        and monitor.name in record.message
        for record in caplog.records
    )


def test_scheduler_logs_notification_exception(caplog):
    monitor = configuration.MonitorItem(
        name="ServiceNotifier",
        url="http://example.com",
        monitor_type="GET",
        interval=60,
        email="ops@example.com",
    )

    def failing_dispatcher(notification):
        raise RuntimeError("dispatch failed")

    scheduler = MonitorScheduler(
        timezone_getter=lambda: 0,
        clock=lambda: datetime.datetime(2023, 1, 1, 0, 0, 0),
        dispatcher=failing_dispatcher,
    )

    with caplog.at_level(logging.ERROR, logger="monitoring.service"):
        event = scheduler.run_single_cycle(monitor, strategy=SequenceStrategy([False]))

    assert event.notification is not None
    assert any(
        "monitor.scheduler.notification_error" in record.message
        and monitor.name in record.message
        for record in caplog.records
    )


def test_scheduler_reuses_state_machine_for_repeated_cycles(monkeypatch):
    monkeypatch.setattr(log_recorder, "record", lambda action, detail: None)
    monkeypatch.setattr(log_recorder, "saveToFile", lambda row, name: None)

    scheduler = MonitorScheduler(
        event_handler=lambda event: None,
        timezone_getter=lambda: 0,
        clock=lambda: datetime.datetime(2023, 1, 1, 0, 0, 0),
    )

    sequence = SequenceStrategy([True, False, False, True])

    def build_monitor(index: int) -> configuration.MonitorItem:
        return configuration.MonitorItem(
            name="PeriodicService",
            url="http://example.com/api",
            monitor_type="GET",
            interval=index,
            email=f"ops+{index}@example.com",
        )

    statuses = []
    machine_sizes = []
    for idx in range(4):
        monitor = build_monitor(idx)
        event = scheduler.run_single_cycle(monitor, strategy=sequence)
        statuses.append(event.status)
        machine_sizes.append(len(scheduler._state_machines))
        assert event.monitor is monitor

    assert statuses == [
        MonitorState.HEALTHY,
        MonitorState.OUTAGE,
        MonitorState.OUTAGE_ONGOING,
        MonitorState.RECOVERED,
    ]
    assert all(size == 1 for size in machine_sizes)

    scheduler.prune_state_machines([])
    assert scheduler._state_machines == {}
