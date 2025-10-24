"""主窗口控制器模块，负责协调 UI 与业务控制器。"""

from __future__ import annotations

import datetime
from typing import Optional, TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

import configuration

from . import ControllerEventBus
from .dashboard import DashboardController
from .preferences import PreferencesController
from monitoring.service import parse_network_address as service_parse_network_address
from ui.main_window import MainWindowUI

if TYPE_CHECKING:
    from ui.theme import ThemeManager


_StatusBarClass = getattr(QtWidgets, "QStatusBar", None)


class _SilentStatusBar:
    def showMessage(self, *_args, **_kwargs):
        return None


class MainWindowController(QtCore.QObject):
    """协调主窗口 UI 与业务逻辑的核心控制器。"""

    def __init__(
        self,
        window: QtWidgets.QMainWindow,
        ui: MainWindowUI,
        theme_manager: "ThemeManager",
    ) -> None:
        super().__init__(window)
        self.window = window
        self.ui = ui
        self.theme_manager = theme_manager

        status_bar: Optional[QtWidgets.QStatusBar]
        status_accessor = getattr(self.window, "statusBar", None)
        if callable(status_accessor):
            try:
                status_bar = status_accessor()
            except Exception:
                status_bar = None
        else:
            status_bar = None

        if status_bar is None and _StatusBarClass is not None and hasattr(self.window, "setStatusBar"):
            try:
                status_bar = _StatusBarClass(self.window)
                self.window.setStatusBar(status_bar)
            except Exception:
                status_bar = None

        if status_bar is None:
            status_bar = _SilentStatusBar()

        self.status = status_bar
        self._monitor_status_label: Optional[QtWidgets.QLabel] = None
        add_permanent = getattr(self.status, "addPermanentWidget", None)
        if callable(add_permanent):
            try:
                label = QtWidgets.QLabel(self.ui.current_status_text())
                label.setObjectName("monitorStateLabel")
                label.setProperty("role", "hint")
                add_permanent(label)
                self._monitor_status_label = label
            except Exception:
                self._monitor_status_label = None
        if hasattr(self.status, "showMessage"):
            self.status.showMessage(self.tr('>>初始化...'), 4000)

        if hasattr(self.window, "setWindowTitle"):
            self.window.setWindowTitle(self.tr('Monitor Everything v1.0'))

        self.events = ControllerEventBus(self)

        self.preferences = PreferencesController(
            window=self.window,
            ui=self.ui,
            theme_manager=self.theme_manager,
            event_bus=self.events,
            parent=self,
        )
        self.dashboard = DashboardController(
            event_bus=self.events,
            timezone=self.preferences.current_timezone,
            parent=self.window,
        )

        self._navigation_shortcuts = self._create_navigation_shortcuts()

        self._current_language = self.preferences.current_language
        self._time_zone = self.preferences.current_timezone
        self._monitoring_active = False

        self.events.logMessage.connect(self._append_log_message)
        self.events.statusMessage.connect(self._show_status_message)
        self.events.monitoringToggled.connect(self._handle_monitoring_toggled)
        self.events.timezoneChanged.connect(self._handle_timezone_changed)
        self.events.languageChanged.connect(self._handle_language_changed)

        self.preferences.setup()

        self.ui.toggleMonitoringButton.clicked.connect(self._on_toggle_monitoring)
        self.ui.reloadConfigButton.clicked.connect(self.reload_configuration)
        self.ui.locationButton.clicked.connect(self.set_location)
        self.ui.exitButton.clicked.connect(self._on_exit_requested)
        self.ui.navigationRequested.connect(self._handle_navigation_request)
        self.ui.themeSelector.currentIndexChanged.connect(self.preferences.on_theme_changed)
        self.ui.languageSelector.currentIndexChanged.connect(self.preferences.on_language_changed)
        self.ui.configWizard.monitorsSaved.connect(self._handle_monitors_saved)
        self.ui.configWizard.requestReload.connect(self._reload_monitors)

        self._clock_timer = QtCore.QTimer(self.window)
        self._clock_timer.timeout.connect(self.update_clock)
        self._clock_timer.start(1000)

        self._reload_monitors()
        self.update_clock()
        self._update_monitor_status_label()

    # --- 事件处理 -----------------------------------------------------
    def _append_log_message(self, message: str) -> None:
        self.ui.monitorBrowser.append(message)
        cursor = self.ui.monitorBrowser.textCursor()
        self.ui.monitorBrowser.moveCursor(cursor.End)
        QtWidgets.QApplication.processEvents()

    def _show_status_message(self, message: str, timeout: int) -> None:
        try:
            self.status.showMessage(message, timeout)
        except Exception:
            pass

    def _handle_monitoring_toggled(self, running: bool) -> None:
        self._monitoring_active = running
        self.ui.update_monitoring_controls(running)
        self._update_monitor_status_label()
        if running:
            self.ui.show_monitor_page()

    def _handle_timezone_changed(self, timezone: int) -> None:
        self._time_zone = timezone
        self.update_clock()

    def _handle_language_changed(self, language: str) -> None:
        self._current_language = language
        self.ui.update_monitoring_controls(self.dashboard.is_running)
        self.preferences.refresh_language_items()
        self.preferences.update_theme_metadata()
        self._update_monitor_status_label()

    def _update_monitor_status_label(self) -> None:
        if self._monitor_status_label is not None:
            try:
                self._monitor_status_label.setText(self.ui.current_status_text())
            except Exception:
                pass

    # --- 导航 ---------------------------------------------------------
    def _create_navigation_shortcuts(self) -> list[QtWidgets.QShortcut]:
        shortcuts: list[QtWidgets.QShortcut] = []
        mapping = {
            "Ctrl+1": "monitor",
            "Ctrl+2": "configuration",
            "Ctrl+3": "preferences",
            "Ctrl+4": "reports",
        }
        try:
            from PyQt5 import QtGui as _QtGui  # type: ignore
        except Exception:  # pragma: no cover - 测试桩环境不提供 QtGui
            _QtGui = None
        key_sequence = getattr(_QtGui, "QKeySequence", None)
        for sequence, nav_id in mapping.items():
            sequence_value = key_sequence(sequence) if callable(key_sequence) else sequence
            shortcut = QtWidgets.QShortcut(sequence_value, self.window)
            shortcut.setContext(QtCore.Qt.ApplicationShortcut)
            shortcut.activated.connect(
                lambda _checked=False, value=nav_id: self._handle_navigation_request(value)
            )
            shortcuts.append(shortcut)
        return shortcuts

    def _handle_navigation_request(self, nav_id: str) -> None:
        if nav_id == "monitor":
            self.ui.show_monitor_page()
        elif nav_id == "configuration":
            self.show_configuration()
        elif nav_id == "preferences":
            self.show_preferences()
        elif nav_id == "reports":
            self.show_reports()

    # --- 按钮行为 -----------------------------------------------------
    def _on_toggle_monitoring(self) -> None:
        if not self.dashboard.is_running:
            try:
                self.dashboard.start_monitoring()
            except ValueError as exc:
                self.events.statusMessage.emit(str(exc), 5000)
        else:
            self.dashboard.stop_monitoring()

    def _on_exit_requested(self) -> None:
        self.dashboard.on_close()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.quit()

    def run_periodically(self, monitor_info) -> None:
        self.dashboard.run_periodically(monitor_info)

    # --- 配置与表单 ---------------------------------------------------
    def show_configuration(self) -> None:
        self._reload_monitors()
        self.ui.show_configuration_page()
        self.events.statusMessage.emit(self.tr('>>配置模式'), 3000)

    def show_preferences(self) -> None:
        self.ui.show_preferences_page()
        self.events.statusMessage.emit(self.tr('>>设置中心'), 3000)

    def show_reports(self) -> None:
        self.ui.show_reports_page()
        self.events.statusMessage.emit(self.tr('>>报表/告警视图预览'), 3000)

    def reload_configuration(self) -> None:
        timeout_error: Optional[Exception] = None
        try:
            configuration.reset_request_timeout_cache()
        except ValueError as exc:
            timeout_error = exc

        self._reload_monitors()

        if timeout_error is None:
            self.events.statusMessage.emit(self.tr('配置已刷新'), 3000)
        else:
            self.events.statusMessage.emit(
                self.tr('配置已刷新，但请求超时配置无效: {error}').format(error=timeout_error),
                5000,
            )

    def set_location(self) -> None:
        self.preferences.choose_timezone()

    def _handle_monitors_saved(self, monitors) -> None:
        try:
            configuration.write_monitor_list(monitors)
        except Exception as exc:
            QMessageBox.critical(self.window, self.tr('保存失败'), str(exc))
            self.events.statusMessage.emit(
                self.tr('保存失败: {error}').format(error=exc), 5000
            )
        else:
            timeout_error: Optional[Exception] = None
            try:
                configuration.reset_request_timeout_cache()
            except ValueError as exc:
                timeout_error = exc

            if timeout_error is None:
                message = self.tr('配置已保存')
                duration = 4000
            else:
                message = self.tr('配置已保存，但请求超时配置无效: {error}').format(
                    error=timeout_error
                )
                duration = 6000

            self.events.statusMessage.emit(message, duration)
            self._reload_monitors()
            self.ui.show_monitor_page()

    def _reload_monitors(self) -> None:
        template_manager = configuration.get_template_manager()
        templates_valid = template_manager.reload()
        monitors = configuration.read_monitor_list()
        self.ui.configWizard.load_monitors(monitors)
        status_messages: list[tuple[str, int]] = []
        if configuration.consume_config_template_created_flag():
            status_messages.append(
                (self.tr('已生成示例配置，请在 Config 目录中填写后重新加载'), 6000)
            )
        if not templates_valid:
            status_messages.append(
                (self.tr('模板配置文件格式无效，已恢复默认文案'), 6000)
            )
        for message, duration in status_messages:
            self.events.statusMessage.emit(message, duration)

    # --- 时钟 ---------------------------------------------------------
    def update_clock(self) -> None:
        utc_time = datetime.datetime.utcnow()
        current_time = utc_time + datetime.timedelta(hours=self._time_zone)
        self.ui.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.ui.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))

    # --- 杂项 ---------------------------------------------------------
    def parse_network_address(self, address):
        return service_parse_network_address(address)

    def on_close(self) -> None:
        self.dashboard.on_close()
        self.preferences.on_close()


__all__ = ["MainWindowController"]
