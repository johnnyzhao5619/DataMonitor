import datetime
import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration  # noqa: E402  pylint: disable=wrong-import-position
import logRecorder  # noqa: E402  pylint: disable=wrong-import-position
from monitoring.service import MonitorScheduler, MonitorStrategy  # noqa: E402
from monitoring.state_machine import (  # noqa: E402
    MonitorState,
    MonitorStateMachine,
    NotificationTemplates,
)


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

    assert len(notifications) == 2
    assert notifications[0].subject.endswith("-outage")
    assert notifications[1].subject.endswith("-recovery")

    assert len(logs) >= 4
    assert any("服务异常" in detail for _, detail in logs)
    assert len(csv_rows) >= 4
