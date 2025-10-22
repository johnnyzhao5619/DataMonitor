"""监控调度层实现。"""

from __future__ import annotations

import datetime as _dt
import threading
from typing import Callable, Dict, Hashable, Iterable, Optional

import apiMonitor
import configuration
import logRecorder
import sendEmail

from .state_machine import (
    MonitorEvent,
    MonitorStateMachine,
    NotificationMessage,
    NotificationTemplates,
)


class MonitorStrategy:
    """执行单次监控检查的策略接口。"""

    def run(self, monitor: configuration.MonitorItem) -> bool:  # pragma: no cover - 接口定义
        raise NotImplementedError


class GetMonitorStrategy(MonitorStrategy):
    def run(self, monitor: configuration.MonitorItem) -> bool:
        return apiMonitor.monitor_get(monitor.url)


class PostMonitorStrategy(MonitorStrategy):
    def run(self, monitor: configuration.MonitorItem) -> bool:
        return apiMonitor.monitor_post(
            monitor.url,
            monitor.payload,
            headers=monitor.headers,
        )


class ServerMonitorStrategy(MonitorStrategy):
    def __init__(self) -> None:
        self._cache: Dict[str, Iterable[str]] = {}

    def run(self, monitor: configuration.MonitorItem) -> bool:
        parsed = self._cache.get(monitor.url)
        if parsed is None:
            parsed = self._parse_network_address(monitor.url)
            self._cache[monitor.url] = parsed
        return apiMonitor.monitor_server(parsed)

    @staticmethod
    def _parse_network_address(address: str):
        protocol = "http"
        url_port_suffix = address

        if address.startswith("http://"):
            url_port_suffix = address[len("http://") :]
        elif address.startswith("https://"):
            protocol = "https"
            url_port_suffix = address[len("https://") :]

        if "/" in url_port_suffix:
            url_port, suffix = url_port_suffix.split("/", 1)
        else:
            url_port = url_port_suffix
            suffix = ""

        if ":" in url_port:
            url, port_str = url_port.split(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = None
        else:
            url = url_port
            port = None

        return protocol, url, port, suffix


class MonitorScheduler:
    """负责协调调度线程、执行策略以及管理状态机。"""

    def __init__(
        self,
        *,
        event_handler: Optional[Callable[[MonitorEvent], None]] = None,
        timezone_getter: Optional[Callable[[], int]] = None,
        clock: Optional[Callable[[], _dt.datetime]] = None,
        templates: Optional[NotificationTemplates] = None,
        dispatcher: Optional[Callable[[NotificationMessage], None]] = None,
    ) -> None:
        self._strategies: Dict[str, MonitorStrategy] = {}
        self._event_handler = event_handler or (lambda event: None)
        self._timezone_getter = timezone_getter or (lambda: 0)
        self._clock = clock or _dt.datetime.utcnow
        self._templates = templates or default_notification_templates()
        self._dispatcher = dispatcher or default_notification_dispatcher
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._state_machines: Dict[Hashable, MonitorStateMachine] = {}

        self.register_strategy("GET", GetMonitorStrategy())
        self.register_strategy("POST", PostMonitorStrategy())
        self.register_strategy("SERVER", ServerMonitorStrategy())

    def register_strategy(self, monitor_type: str, strategy: MonitorStrategy) -> None:
        self._strategies[monitor_type.upper()] = strategy

    def start(self, monitors: Iterable[configuration.MonitorItem]) -> None:
        if self._threads:
            raise RuntimeError("调度器已经在运行")

        self._stop_event.clear()
        for monitor in monitors:
            strategy = self._strategies.get(monitor.monitor_type.upper())
            if strategy is None:
                raise ValueError(f"未注册监控类型 {monitor.monitor_type}")

            thread = threading.Thread(
                name=monitor.name,
                target=self._run_monitor,
                args=(monitor, strategy),
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join()
        self._threads.clear()
        self._state_machines.clear()

    def _run_monitor(
        self,
        monitor: configuration.MonitorItem,
        strategy: MonitorStrategy,
    ) -> None:
        key = self._monitor_key(monitor)
        state_machine = self._state_machines.setdefault(
            key,
            MonitorStateMachine(monitor, self._templates),
        )

        try:
            while not self._stop_event.is_set():
                try:
                    success = bool(strategy.run(monitor))
                except Exception as exc:  # pragma: no cover - 防御性兜底
                    success = False
                    print(f"执行监控 {monitor.name} 发生异常: {exc}")

                utc_now, local_now = self._now()
                event = state_machine.transition(success, utc_now, local_now)
                self._handle_event(event)

                interval_seconds = max(float(monitor.interval), 0.0)
                if interval_seconds == 0:
                    continue
                if self._stop_event.wait(interval_seconds):
                    break
        finally:
            # 清理已完成监控的状态机实例，避免悬挂引用。
            self._state_machines.pop(key, None)

    def _monitor_key(self, monitor: configuration.MonitorItem) -> Hashable:
        """生成用于缓存状态机的可哈希键。"""

        return id(monitor)

    def _now(self) -> tuple[_dt.datetime, _dt.datetime]:
        utc_now = self._clock()
        try:
            offset = int(self._timezone_getter())
        except (TypeError, ValueError):  # pragma: no cover - 防御性兜底
            offset = 0
        local_now = utc_now + _dt.timedelta(hours=offset)
        return utc_now, local_now

    def _handle_event(self, event: MonitorEvent) -> None:
        self._write_logs(event)
        self._dispatch_notification(event)
        try:
            self._event_handler(event)
        except Exception as exc:  # pragma: no cover - 防御性兜底
            print(f"处理监控事件时发生异常: {exc}")

    def _write_logs(self, event: MonitorEvent) -> None:
        logRecorder.record(event.log_action, event.log_detail)
        logRecorder.saveToFile(list(event.csv_row), event.monitor.name)

    def _dispatch_notification(self, event: MonitorEvent) -> None:
        if not event.notification:
            return
        try:
            self._dispatcher(event.notification)
        except Exception as exc:  # pragma: no cover - 防御性兜底
            print(f"发送通知失败: {exc}")


def default_notification_templates() -> NotificationTemplates:
    return NotificationTemplates(
        channel="email",
        build_outage=sendEmail.build_outage_alert_message,
        build_recovery=sendEmail.build_outage_recovery_message,
    )


def default_notification_dispatcher(notification: NotificationMessage) -> None:
    if notification.channel != "email":
        raise ValueError(f"未知通知渠道: {notification.channel}")
    sendEmail.send_email(
        notification.subject,
        notification.body,
        recipients=notification.recipients,
    )
