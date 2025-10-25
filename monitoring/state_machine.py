# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 11:53 p.m.
# @Author: John Zhao
"""Monitoring state machine definitions."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional, Tuple

from PySide6 import QtCore

import configuration
from configuration import MonitorItem


class MonitorState(Enum):
    """Describe the business state produced by a monitor run."""

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
            MonitorState.HEALTHY:
            translate("MonitorState", "Service healthy"),
            MonitorState.RECOVERED:
            translate("MonitorState", "Service recovered"),
            MonitorState.OUTAGE:
            translate("MonitorState", "Service outage"),
            MonitorState.OUTAGE_ONGOING:
            translate("MonitorState", "Service outage ongoing"),
        }[self]

    @property
    def csv_label(self) -> str:
        translate = QtCore.QCoreApplication.translate
        return {
            MonitorState.HEALTHY:
            translate("MonitorState", "Healthy"),
            MonitorState.RECOVERED:
            translate("MonitorState", "Recovered"),
            MonitorState.OUTAGE:
            translate("MonitorState", "Outage"),
            MonitorState.OUTAGE_ONGOING:
            translate("MonitorState", "Outage ongoing"),
        }[self]

    @property
    def status_bar_text(self) -> str:
        translate = QtCore.QCoreApplication.translate
        if self in (MonitorState.HEALTHY, MonitorState.RECOVERED):
            return translate("MonitorState", ">>>Running...")
        return translate("MonitorState", "Service outage detected")


@dataclass(frozen=True)
class NotificationMessage:
    """Describe the contents of a notification to be delivered."""

    channel: str
    subject: str
    body: str
    recipients: Optional[str] = None


@dataclass(frozen=True)
class NotificationTemplates:
    """Provide builders for notifications associated with monitor states."""

    channel: str
    build_outage: Callable[[str, _dt.datetime, Optional[str]], Tuple[str, str]]
    build_recovery: Callable[[str, _dt.datetime, Optional[str]], Tuple[str,
                                                                       str]]


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
    """Drive state transitions from monitor results and emit log/notification data."""

    def __init__(self, monitor: MonitorItem, templates: NotificationTemplates):
        self._monitor = monitor
        self._templates = templates
        self._last_success = True

    @property
    def monitor(self) -> MonitorItem:
        """Return the monitor currently bound to this machine."""

        return self._monitor

    def update_monitor(self, monitor: MonitorItem) -> None:
        """Update the monitor information attached to the state machine."""

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

    def _build_context(self, state: MonitorState,
                       local_time: _dt.datetime) -> Dict[str, object]:
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
            self, state: MonitorState,
            local_time: _dt.datetime) -> Optional[NotificationMessage]:
        recipients = self._monitor.normalised_email()
        if state is MonitorState.OUTAGE:
            subject, body = self._templates.build_outage(
                self._monitor.name, local_time, self._monitor.language)
        elif state is MonitorState.RECOVERED:
            subject, body = self._templates.build_recovery(
                self._monitor.name, local_time, self._monitor.language)
        else:
            return None

        return NotificationMessage(
            channel=self._templates.channel,
            subject=subject,
            body=body,
            recipients=recipients,
        )

    def _build_message(self, context: Dict[str, object]) -> str:
        return configuration.render_template("ui",
                                             "status_line",
                                             context,
                                             language=self._monitor.language)

    def _build_log_action(self, context: Dict[str, object]) -> str:
        return configuration.render_template("log",
                                             "action_line",
                                             context,
                                             language=self._monitor.language)

    def _build_log_detail(self, context: Dict[str, object]) -> str:
        return configuration.render_template("log",
                                             "detail_line",
                                             context,
                                             language=self._monitor.language)

    def _build_status_bar_message(self, state: MonitorState) -> str:
        if state in (MonitorState.HEALTHY, MonitorState.RECOVERED):
            return MonitorState.HEALTHY.status_bar_text
        return f"{self._monitor.name} {MonitorState.OUTAGE.status_bar_text}"
