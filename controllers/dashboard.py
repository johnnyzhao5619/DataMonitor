"""监控调度与周期任务控制器。"""

from __future__ import annotations

import threading
from typing import Dict, Optional, Tuple

from PyQt5 import QtCore

import configuration
import logRecorder
from configuration import SUPPORTED_MONITOR_TYPES
from monitoring.service import (
    MonitorScheduler,
    parse_network_address as service_parse_network_address,
)
from monitoring.state_machine import MonitorEvent

from . import ControllerEventBus


PeriodicMonitorKey = Tuple[str, str, str]


class DashboardController(QtCore.QObject):
    """负责监控调度器与周期任务管理。"""

    def __init__(
        self,
        *,
        event_bus: ControllerEventBus,
        timezone: int = 0,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._event_bus = event_bus
        self._timezone = timezone
        self._scheduler: Optional[MonitorScheduler] = None
        self._periodic_scheduler = self._create_scheduler()
        self._periodic_monitors: Dict[PeriodicMonitorKey, configuration.MonitorItem] = {}
        self._periodic_timers: Dict[PeriodicMonitorKey, QtCore.QTimer] = {}
        self._running_periodic: set[PeriodicMonitorKey] = set()

        self._event_bus.timezoneChanged.connect(self._on_timezone_changed)

    # --- 公开属性 ----------------------------------------------------
    @property
    def is_running(self) -> bool:
        return self._scheduler is not None

    # --- 主监控调度 --------------------------------------------------
    def start_monitoring(self) -> bool:
        if self._scheduler is not None:
            raise RuntimeError(self.tr("监控已经在运行"))

        monitors = configuration.read_monitor_list()
        overview = self.tr("目前读取到{count}个监控项，分别是：").format(
            count=len(monitors)
        )
        self._event_bus.logMessage.emit(overview)
        for index, monitor in enumerate(monitors, start=1):
            self._event_bus.logMessage.emit(
                self.tr(
                    "{index}. {name} --- 类型: {monitor_type} --- 地址: {url} --- 周期: {interval}秒"
                ).format(
                    index=index,
                    name=monitor.name,
                    monitor_type=monitor.monitor_type,
                    url=monitor.url,
                    interval=monitor.interval,
                )
            )

        if not monitors:
            self._event_bus.statusMessage.emit(self.tr("未读取到有效的监控配置"), 4000)
            return False

        scheduler = self._create_scheduler()
        scheduler.start(monitors)
        self._scheduler = scheduler
        self._event_bus.monitoringToggled.emit(True)
        self._event_bus.statusMessage.emit(self.tr("监控已启动"), 3000)
        return True

    def stop_monitoring(self) -> None:
        scheduler = self._scheduler
        if scheduler is None:
            return

        scheduler.stop()
        self._scheduler = None
        self._event_bus.monitoringToggled.emit(False)
        self._event_bus.statusMessage.emit(self.tr("监控已停止"), 3000)

    def on_close(self) -> None:
        self.stop_monitoring()
        self._stop_periodic_monitors()

    # --- 周期任务 ----------------------------------------------------
    def run_periodically(self, monitor_info) -> None:
        monitor = self._build_monitor_item(monitor_info)
        if monitor is None:
            return

        monitor_key = self._make_periodic_key(monitor)
        self._periodic_monitors[monitor_key] = monitor
        self._trigger_periodic_monitor(monitor_key)
        self._schedule_periodic_monitor(monitor, monitor_key)

    def _trigger_periodic_monitor(self, monitor_key: PeriodicMonitorKey) -> None:
        monitor = self._periodic_monitors.get(monitor_key)
        if not monitor:
            timer = self._periodic_timers.pop(monitor_key, None)
            if timer:
                timer.stop()
            return

        if monitor_key in self._running_periodic:
            return

        self._running_periodic.add(monitor_key)

        def _run_cycle() -> None:
            try:
                self._periodic_scheduler.run_single_cycle(monitor)
            finally:
                self._running_periodic.discard(monitor_key)

        thread = threading.Thread(
            name=f"Monitor:{monitor.name}",
            target=_run_cycle,
            daemon=True,
        )
        thread.start()

    def _schedule_periodic_monitor(
        self,
        monitor: configuration.MonitorItem,
        monitor_key: PeriodicMonitorKey,
    ) -> None:
        interval_ms = max(int(monitor.interval), 0) * 1000
        timer = self._periodic_timers.get(monitor_key)

        if interval_ms == 0:
            if timer:
                timer.stop()
            return

        if timer is None:
            timer = QtCore.QTimer(self.parent())
            timer.setSingleShot(False)
            timer.timeout.connect(lambda key=monitor_key: self._trigger_periodic_monitor(key))
            self._periodic_timers[monitor_key] = timer

        timer.setInterval(interval_ms)
        if not timer.isActive():
            timer.start()

    def _stop_periodic_monitors(self) -> None:
        for timer in self._periodic_timers.values():
            timer.stop()
        self._periodic_timers.clear()
        self._periodic_monitors.clear()
        self._running_periodic.clear()
        self._periodic_scheduler.stop()
        self._periodic_scheduler = self._create_scheduler()

    # --- 工具方法 ----------------------------------------------------
    def _create_scheduler(self) -> MonitorScheduler:
        return MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self._timezone,
        )

    def _handle_monitor_event(self, event: MonitorEvent) -> None:
        self._event_bus.logMessage.emit(event.message)
        if event.status_bar_message:
            self._event_bus.statusMessage.emit(event.status_bar_message, 4000)

    def _on_timezone_changed(self, timezone: int) -> None:
        self._timezone = timezone

    def _build_monitor_item(self, monitor_info):
        if isinstance(monitor_info, configuration.MonitorItem):
            return monitor_info

        name = monitor_info.get("name")
        url = monitor_info.get("url")
        if not name or not url:
            self._event_bus.logMessage.emit(self.tr("监控项配置缺少名称或地址"))
            return None

        raw_type = monitor_info.get("type")
        monitor_type = ""
        if isinstance(raw_type, str):
            monitor_type = raw_type.strip().upper()
        elif raw_type is None:
            monitor_type = ""
        else:
            self._log_unsupported_type(raw_type, url, name=name)
            return None

        if monitor_type not in SUPPORTED_MONITOR_TYPES:
            self._log_unsupported_type(monitor_type or raw_type, url, name=name)
            return None

        try:
            interval = int(monitor_info.get("interval", 0))
        except (TypeError, ValueError):
            self._event_bus.logMessage.emit(
                self.tr("监控项[{name}]的周期配置无效: {value}").format(
                    name=name, value=monitor_info.get("interval")
                )
            )
            return None

        return configuration.MonitorItem(
            name=name,
            url=url,
            monitor_type=monitor_type,
            interval=interval,
            email=monitor_info.get("email"),
            payload=monitor_info.get("payload"),
            headers=monitor_info.get("headers"),
        )

    def _make_periodic_key(self, monitor: configuration.MonitorItem) -> PeriodicMonitorKey:
        return (monitor.name, monitor.url, monitor.monitor_type)

    def _log_unsupported_type(self, monitor_type, url, *, name=None):
        monitor_name = f"[{name}]" if name else ""
        readable_type = monitor_type if monitor_type not in (None, "") else "<empty>"
        message = self.tr("监控项{monitor_name}类型 '{monitor_type}' 未被支持，URL: {url}").format(
            monitor_name=monitor_name,
            monitor_type=readable_type,
            url=url,
        )
        logRecorder.record("Unsupported Monitor Type", message)
        self._event_bus.logMessage.emit(message)
        self._event_bus.statusMessage.emit(message, 5000)
        return message

    @staticmethod
    def parse_network_address(address: str):
        return service_parse_network_address(address)


__all__ = ["DashboardController", "PeriodicMonitorKey"]
