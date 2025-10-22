from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.main_window import MainWindowUI
from ui.theme import ThemeManager, teams_dark, teams_light
import apiMonitor
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import datetime
import logRecorder
import sys
import queue
import threading
from pathlib import Path
from typing import Optional, Tuple

from monitoring.service import (
    MonitorScheduler,
    parse_network_address as service_parse_network_address,
)
from monitoring.state_machine import MonitorEvent


PeriodicMonitorKey = Tuple[str, str, str]


class MainWindowController(QtCore.QObject):
    """协调主窗口 UI 与业务逻辑的控制器。"""

    def __init__(
        self,
        window: QtWidgets.QMainWindow,
        ui: MainWindowUI,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__(window)
        self.window = window
        self.ui = ui
        self.theme_manager = theme_manager

        self.status = self.window.statusBar()
        self.status.showMessage('>>初始化...', 4000)
        self.window.setWindowTitle('Monitor Everything v0.2')

        self.switch_status = True
        self.printf_queue: queue.Queue = queue.Queue()
        self.time_zone = self._read_config_timezone()
        self.scheduler: Optional[MonitorScheduler] = None
        self._periodic_scheduler = MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self.time_zone,
        )
        self._periodic_monitors: dict[PeriodicMonitorKey, configuration.MonitorItem] = {}
        self._periodic_timers: dict[PeriodicMonitorKey, QtCore.QTimer] = {}
        self._running_periodic: set[PeriodicMonitorKey] = set()

        self._clock_timer = QtCore.QTimer(self.window)
        self._clock_timer.timeout.connect(self.update_clock)
        self._clock_timer.start(1000)

        self.ui.switchButton.clicked.connect(self.start_monitor)
        self.ui.configButton.clicked.connect(self.show_configuration)
        self.ui.locationButton.clicked.connect(self.set_location)
        self.ui.configWizard.monitorsSaved.connect(self._handle_monitors_saved)
        self.ui.configWizard.requestReload.connect(self._reload_monitors)

        self._initialise_theme_selector()

        self._reload_monitors()
        self._update_timezone_display()
        self.update_clock()

    def start_monitor(self) -> None:
        if self.switch_status is True:
            monitor_list = configuration.read_monitor_list()
            self.printf_queue.put(f"目前读取到{len(monitor_list)}个监控项，分别是：")
            for index, monitor in enumerate(monitor_list, start=1):
                self.printf_queue.put(
                    f"{index}. {monitor.name} --- 类型: {monitor.monitor_type} --- 地址: {monitor.url} --- 周期: {monitor.interval}秒"
                )

            if not monitor_list:
                self.status.showMessage('未读取到有效的监控配置')
                return

            self.scheduler = MonitorScheduler(
                event_handler=self._handle_monitor_event,
                timezone_getter=lambda: self.time_zone,
            )
            self.scheduler.start(monitor_list)

            self.ui.show_monitor_page()
            self.ui.switchButton.setText('关闭 Close')
            self.switch_status = False
        else:
            if self.scheduler:
                self.scheduler.stop()
            QtWidgets.QApplication.quit()

    def show_configuration(self) -> None:
        self._reload_monitors()
        self.ui.show_configuration_page()
        self.status.showMessage('>>配置模式', 3000)

    def set_location(self) -> None:
        time_zone, ok = QInputDialog.getInt(
            self.window,
            "输入时区",
            "请输入所在时区(整数):",
            self.time_zone,
            -12,
            14,
            1,
        )
        if ok:
            self.time_zone = time_zone
            configuration.set_timezone(str(time_zone))
            self._update_timezone_display()
            self.update_clock()

    def update_clock(self) -> None:
        utc_time = datetime.datetime.utcnow()
        current_time = utc_time + datetime.timedelta(hours=self.time_zone)
        self.ui.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.ui.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))

        while True:
            try:
                message = self.printf_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.ui.monitorBrowser.append(message)
                cursor = self.ui.monitorBrowser.textCursor()
                self.ui.monitorBrowser.moveCursor(cursor.End)
                QtWidgets.QApplication.processEvents()

    def _initialise_theme_selector(self) -> None:
        selector = self.ui.themeSelector
        names = self.theme_manager.available_themes()
        selector.blockSignals(True)
        selector.clear()
        selector.addItems(names)

        current = self.theme_manager.current_theme_name()
        if current is None and names:
            current = names[0]
            self.theme_manager.apply_theme(current)

        if current:
            index = selector.findText(current)
            if index >= 0:
                selector.setCurrentIndex(index)

        selector.blockSignals(False)
        selector.currentTextChanged.connect(self._on_theme_changed)
        self._refresh_theme_widgets()

    def _on_theme_changed(self, name: str) -> None:
        if not name:
            return

        previous = self.theme_manager.current_theme_name()
        if previous != name:
            self.theme_manager.apply_theme(name)

        self._refresh_theme_widgets()
        self.status.showMessage(f'已切换至主题: {name}', 3000)

    def _refresh_theme_widgets(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        for widget in (
            self.window,
            self.ui.central_widget,
            self.ui.navigationBar,
            self.ui.contentStack,
            self.ui.monitorBrowser,
            self.ui.configWizard,
        ):
            if widget is None:
                continue
            app.style().unpolish(widget)
            app.style().polish(widget)
            widget.update()

    def _handle_monitor_event(self, event: MonitorEvent) -> None:
        self.printf_queue.put(event.message)
        if event.status_bar_message:
            self.status.showMessage(event.status_bar_message)

    def perform_task(self, url, parsed_address, monitor_type, email, payload=None, *, headers=None):
        monitor_type_normalised = str(monitor_type).strip().upper() if monitor_type else ""
        if monitor_type_normalised == "GET":
            return apiMonitor.monitor_get(url)
        if monitor_type_normalised == "POST":
            return apiMonitor.monitor_post(url, payload, headers=headers)
        if monitor_type_normalised == "SERVER":
            address = parsed_address or service_parse_network_address(url)
            return apiMonitor.monitor_server(address)

        self._log_unsupported_type(monitor_type, url)
        return False

    def _log_unsupported_type(self, monitor_type, url, name=None):
        monitor_name = f"[{name}]" if name else ""
        readable_type = monitor_type if monitor_type not in (None, "") else "<empty>"
        message = f"监控项{monitor_name}类型 '{readable_type}' 未被支持，URL: {url}"
        logRecorder.record("Unsupported Monitor Type", message)
        self.printf_queue.put(message)
        try:
            self.status.showMessage(message)
        except Exception:
            pass
        return message

    def parse_network_address(self, address):
        """解析网络地址字符串。"""

        return service_parse_network_address(address)

    def run_periodically(self, monitorInfo):
        monitor = self._build_monitor_item(monitorInfo)
        if monitor is None:
            return

        key = self._make_periodic_key(monitor)
        self._periodic_monitors[key] = monitor
        self._trigger_periodic_monitor(key)
        self._schedule_periodic_monitor(monitor, key)

    def _handle_monitors_saved(self, monitors):
        try:
            configuration.write_monitor_list(monitors)
        except Exception as exc:
            QMessageBox.critical(self.window, '保存失败', str(exc))
            self.status.showMessage(f'保存失败: {exc}', 5000)
        else:
            self.status.showMessage('配置已保存', 4000)
            self._reload_monitors()
            self.ui.show_monitor_page()

    def _reload_monitors(self):
        monitors = configuration.read_monitor_list()
        self.ui.configWizard.load_monitors(monitors)

    def _read_config_timezone(self):
        raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self):
        self.ui.localTimeGroupBox.setTitle(f'本地时间 Local Time(时区 Time Zone: {self.time_zone})')

    def on_close(self) -> None:
        if self.scheduler:
            self.scheduler.stop()
        self._stop_periodic_monitors()

    def _build_monitor_item(self, monitorInfo):
        if isinstance(monitorInfo, configuration.MonitorItem):
            return monitorInfo

        name = monitorInfo.get("name")
        url = monitorInfo.get("url")
        if not name or not url:
            self.printf_queue.put("监控项配置缺少名称或地址")
            return None

        raw_type = monitorInfo.get("type")
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
            interval = int(monitorInfo.get("interval", 0))
        except (TypeError, ValueError):
            self.printf_queue.put(f"监控项[{name}]的周期配置无效: {monitorInfo.get('interval')}")
            return None

        return configuration.MonitorItem(
            name=name,
            url=url,
            monitor_type=monitor_type,
            interval=interval,
            email=monitorInfo.get("email"),
            payload=monitorInfo.get("payload"),
            headers=monitorInfo.get("headers"),
        )

    def _make_periodic_key(self, monitor: configuration.MonitorItem) -> PeriodicMonitorKey:
        return (monitor.name, monitor.url, monitor.monitor_type)

    def _trigger_periodic_monitor(self, monitor_key: PeriodicMonitorKey):
        monitor = self._periodic_monitors.get(monitor_key)
        if not monitor:
            timer = self._periodic_timers.pop(monitor_key, None)
            if timer:
                timer.stop()
            return

        if monitor_key in self._running_periodic:
            return

        self._running_periodic.add(monitor_key)

        def _run_cycle():
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
    ):
        interval_ms = max(int(monitor.interval), 0) * 1000
        timer = self._periodic_timers.get(monitor_key)

        if interval_ms == 0:
            if timer:
                timer.stop()
            return

        if timer is None:
            timer = QtCore.QTimer(self.window)
            timer.setSingleShot(False)
            timer.timeout.connect(
                lambda key=monitor_key: self._trigger_periodic_monitor(key)
            )
            self._periodic_timers[monitor_key] = timer

        timer.setInterval(interval_ms)
        if not timer.isActive():
            timer.start()

    def _stop_periodic_monitors(self):
        for timer in self._periodic_timers.values():
            timer.stop()
        self._periodic_timers.clear()
        self._periodic_monitors.clear()
        self._running_periodic.clear()
        self._periodic_scheduler.stop()
        self._periodic_scheduler = MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self.time_zone,
        )


class toolsetWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)
        self.theme_manager = ThemeManager()
        self.theme_manager.register_many((teams_light, teams_dark))
        self.theme_manager.apply_theme(teams_light.name)
        self.controller = MainWindowController(self, self.ui, self.theme_manager)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            controller = super().__getattribute__("controller")
            if hasattr(controller, item):
                return getattr(controller, item)
            raise

    def closeEvent(self, event):
        self.controller.on_close()
        super().closeEvent(event)


if __name__ == '__main__':
    log_root = Path(configuration.get_logdir())
    folder = log_root / "Log"
    configDir = log_root / "Config"

    folder.mkdir(parents=True, exist_ok=True)
    if not configDir.exists():
        configDir.mkdir(parents=True, exist_ok=True)
        configuration.writeconfig(str(configDir))
    elif not (configDir / "Config.ini").exists():
        configuration.writeconfig(str(configDir))

    print("folder:", folder)
    print("configDir:", configDir)
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = toolsetWindow()
    mainWindow.show()
    sys.exit(app.exec_())
