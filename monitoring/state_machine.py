"""监控状态机定义。"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional, Tuple

from PySide6 import QtCore

import configuration
from configuration import MonitorItem


class MonitorState(Enum):
    """描述监控执行后的业务状态。"""

    HEALTHY = "healthy"
    RECOVERED = "recovered"
    OUTAGE = "outage"
    OUTAGE_ONGOING = "outage_ongoing"

    @property
    def response_code(self) -> int:
        return {
            MonitorState.HEALTHY: 1,
            MonitorState.RECOVERED: 2,
            MonitorState.OUTAGE: 3,
            MonitorState.OUTAGE_ONGOING: 4,
        }[self]

    @property
    def display_text(self) -> str:
        translate = QtCore.QCoreApplication.translate
        return {
            MonitorState.HEALTHY: translate("MonitorState", "服务正常"),
            MonitorState.RECOVERED: translate("MonitorState", "服务恢复"),
            MonitorState.OUTAGE: translate("MonitorState", "服务异常"),
            MonitorState.OUTAGE_ONGOING: translate("MonitorState", "服务持续异常"),
        }[self]

    @property
    def csv_label(self) -> str:
        translate = QtCore.QCoreApplication.translate
        return {
            MonitorState.HEALTHY: translate("MonitorState", "正常"),
            MonitorState.RECOVERED: translate("MonitorState", "恢复"),
            MonitorState.OUTAGE: translate("MonitorState", "异常"),
            MonitorState.OUTAGE_ONGOING: translate("MonitorState", "持续异常"),
        }[self]

    @property
    def status_bar_text(self) -> str:
        translate = QtCore.QCoreApplication.translate
        if self in (MonitorState.HEALTHY, MonitorState.RECOVERED):
            return translate("MonitorState", ">>>运行中...")
        return translate("MonitorState", "服务异常")


@dataclass(frozen=True)
class NotificationMessage:
    """描述待发送的通知内容。"""

    channel: str
    subject: str
    body: str
    recipients: Optional[str] = None


@dataclass(frozen=True)
class NotificationTemplates:
    """用于构建不同状态对应的通知文案。"""

    channel: str
    build_outage: Callable[[str, _dt.datetime, Optional[str]], Tuple[str, str]]
    build_recovery: Callable[[str, _dt.datetime, Optional[str]], Tuple[str, str]]


@dataclass(frozen=True)
class MonitorEvent:
    monitor: MonitorItem
    status: MonitorState
    success: bool
    utc_time: _dt.datetime
    local_time: _dt.datetime
    message: str
    status_bar_message: str
    log_action: str
    log_detail: str
    csv_row: Tuple[object, ...]
    notification: Optional[NotificationMessage]
    is_status_change: bool


class MonitorStateMachine:
    """根据监控结果驱动状态切换，并产生日志/通知信息。"""

    def __init__(self, monitor: MonitorItem, templates: NotificationTemplates):
        self._monitor = monitor
        self._templates = templates
        self._last_success = True

    @property
    def monitor(self) -> MonitorItem:
        """返回当前绑定的监控项。"""

        return self._monitor

    def update_monitor(self, monitor: MonitorItem) -> None:
        """更新状态机绑定的监控项信息。"""

        self._monitor = monitor

    def transition(
        self,
        success: bool,
        utc_time: _dt.datetime,
        local_time: _dt.datetime,
    ) -> MonitorEvent:
        previous_success = self._last_success
        self._last_success = success

        if success and previous_success:
            state = MonitorState.HEALTHY
            notification = None
        elif success and not previous_success:
            state = MonitorState.RECOVERED
            notification = self._build_notification(state, local_time)
        elif not success and previous_success:
            state = MonitorState.OUTAGE
            notification = self._build_notification(state, local_time)
        else:
            state = MonitorState.OUTAGE_ONGOING
            notification = None

        context = self._build_context(state, local_time)
        message = self._build_message(context)
        log_action = self._build_log_action(context)
        log_detail = self._build_log_detail(context)
        csv_row = (
            local_time,
            context["service_name"],
            context["monitor_type"],
            context["url"],
            context["interval"],
            context["status_code"],
            context["status_text"],
        )
        status_bar_message = self._build_status_bar_message(state)

        return MonitorEvent(
            monitor=self._monitor,
            status=state,
            success=success,
            utc_time=utc_time,
            local_time=local_time,
            message=message,
            status_bar_message=status_bar_message,
            log_action=log_action,
            log_detail=log_detail,
            csv_row=csv_row,
            notification=notification,
            is_status_change=success != previous_success,
        )

    def _build_context(
        self, state: MonitorState, local_time: _dt.datetime
    ) -> Dict[str, object]:
        timestamp_text = local_time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "service_name": self._monitor.name,
            "monitor_type": self._monitor.monitor_type,
            "url": self._monitor.url,
            "interval": self._monitor.interval,
            "status_code": state.response_code,
            "status_label": state.display_text,
            "status_text": state.csv_label,
            "event_timestamp": timestamp_text,
        }

    def _build_notification(
        self, state: MonitorState, local_time: _dt.datetime
    ) -> Optional[NotificationMessage]:
        recipients = self._monitor.normalised_email()
        if state is MonitorState.OUTAGE:
            subject, body = self._templates.build_outage(
                self._monitor.name, local_time, self._monitor.language
            )
        elif state is MonitorState.RECOVERED:
            subject, body = self._templates.build_recovery(
                self._monitor.name, local_time, self._monitor.language
            )
        else:
            return None

        return NotificationMessage(
            channel=self._templates.channel,
            subject=subject,
            body=body,
            recipients=recipients,
        )

    def _build_message(self, context: Dict[str, object]) -> str:
        return configuration.render_template(
            "ui", "status_line", context, language=self._monitor.language
        )

    def _build_log_action(self, context: Dict[str, object]) -> str:
        return configuration.render_template(
            "log", "action_line", context, language=self._monitor.language
        )

    def _build_log_detail(self, context: Dict[str, object]) -> str:
        return configuration.render_template(
            "log", "detail_line", context, language=self._monitor.language
        )

    def _build_status_bar_message(self, state: MonitorState) -> str:
        if state in (MonitorState.HEALTHY, MonitorState.RECOVERED):
            return MonitorState.HEALTHY.status_bar_text
        return f"{self._monitor.name}{MonitorState.OUTAGE.status_bar_text}"
