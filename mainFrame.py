from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.main_window import MainWindowUI
import apiMonitor
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import datetime
import logRecorder
import sys
import queue
import threading
from pathlib import Path
from typing import Optional

from monitoring.service import (
    MonitorScheduler,
    ServerMonitorStrategy,
)
from monitoring.state_machine import MonitorEvent


class toolsetWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)
        self.status = self.statusBar()
        self.status.showMessage('>>初始化...', 4000)
        self.setWindowTitle('Monitor Everything v0.2')
        self.ui.switchButton.clicked.connect(self.start_monitor)
        self.ui.configButton.clicked.connect(self.show_configuration)
        self.ui.locationButton.clicked.connect(self.set_location)
        self.ui.configWizard.monitorsSaved.connect(self._handle_monitors_saved)
        self.ui.configWizard.requestReload.connect(self._reload_monitors)

        self.switch_status = True
        self.printf_queue = queue.Queue()
        self.time_zone = self._read_config_timezone()
        self._clock_timer = QtCore.QTimer(self)
        self._clock_timer.timeout.connect(self.update_clock)
        self._clock_timer.start(1000)
        self._reload_monitors()
        self._update_timezone_display()
        self.update_clock()
        self.scheduler: Optional[MonitorScheduler] = None
        self._periodic_scheduler = MonitorScheduler(
            event_handler=self._handle_monitor_event,
            timezone_getter=lambda: self.time_zone,
        )
        self._periodic_monitors: dict[str, configuration.MonitorItem] = {}
        self._periodic_timers: dict[str, QtCore.QTimer] = {}
        self._running_periodic: set[str] = set()

    def start_monitor(self):
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
        elif self.switch_status is False:
            if self.scheduler:
                self.scheduler.stop()
            QtWidgets.QApplication.quit()

    def show_configuration(self):
        self._reload_monitors()
        self.ui.show_configuration_page()
        self.status.showMessage('>>配置模式', 3000)

    def set_location(self):
        # 后面四个数字的作用依次是 初始值 最小值 最大值 步幅
        time_zone, ok = QInputDialog.getInt(self, "输入时区", "请输入所在时区(整数):", self.time_zone, -12, 14, 1)
        if ok:
            self.time_zone = time_zone
            configuration.set_timezone(str(time_zone))
            self._update_timezone_display()
            self.update_clock()
        # self.echo(time_zone)

    def update_clock(self):
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

    def _handle_monitor_event(self, event: MonitorEvent):
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
            address = parsed_address
            if address is None:
                address = ServerMonitorStrategy._parse_network_address(url)
            return apiMonitor.monitor_server(address)

        self._log_unsupported_type(monitor_type, url)
        return False

    def _log_unsupported_type(self, monitor_type, url, name=None):
        monitor_name = f"[{name}]" if name else ""
        readable_type = monitor_type if monitor_type not in (None, "") else "<empty>"
        message = f"监控项{monitor_name}类型 '{readable_type}' 未被支持，URL: {url}"
        logRecorder.record("Unsupported Monitor Type", message)
        if hasattr(self, "printf_queue"):
            self.printf_queue.put(message)
        if hasattr(self, "status"):
            try:
                self.status.showMessage(message)
            except Exception:
                pass
        return message

    # 格式化url
    def parse_network_address(self, address):
        """
        解析网络地址字符串，返回协议、主机、端口和路径后缀。
        """
        protocol = 'http'
        url_port_suffix = address

        if address.startswith("http://"):
            url_port_suffix = address[len("http://"):]
        elif address.startswith("https://"):
            protocol = 'https'
            url_port_suffix = address[len("https://"):]

        print("url_port_suffix:", url_port_suffix)

        if '/' in url_port_suffix:
            url_port, suffix = url_port_suffix.split('/', 1)
        else:
            url_port = url_port_suffix
            suffix = ''

        if ':' in url_port:
            url, port_str = url_port.split(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = None
        else:
            url = url_port
            port = None

        return [protocol, url, port, suffix]

    # 周期性运行
    def run_periodically(self, monitorInfo):
        monitor = self._build_monitor_item(monitorInfo)
        if monitor is None:
            return

        self._periodic_monitors[monitor.name] = monitor
        self._trigger_periodic_monitor(monitor.name)
        self._schedule_periodic_monitor(monitor)

    def _handle_monitors_saved(self, monitors):
        try:
            configuration.write_monitor_list(monitors)
        except Exception as exc:
            QMessageBox.critical(self, '保存失败', str(exc))
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

    def closeEvent(self, event):
        if self.scheduler:
            self.scheduler.stop()
        self._stop_periodic_monitors()
        super().closeEvent(event)

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

    def _trigger_periodic_monitor(self, monitor_name: str):
        monitor = self._periodic_monitors.get(monitor_name)
        if not monitor:
            timer = self._periodic_timers.pop(monitor_name, None)
            if timer:
                timer.stop()
            return

        if monitor_name in self._running_periodic:
            return

        self._running_periodic.add(monitor_name)

        def _run_cycle():
            try:
                self._periodic_scheduler.run_single_cycle(monitor)
            finally:
                self._running_periodic.discard(monitor_name)

        thread = threading.Thread(
            name=f"Monitor:{monitor.name}",
            target=_run_cycle,
            daemon=True,
        )
        thread.start()

    def _schedule_periodic_monitor(self, monitor: configuration.MonitorItem):
        interval_ms = max(int(monitor.interval), 0) * 1000
        timer = self._periodic_timers.get(monitor.name)

        if interval_ms == 0:
            if timer:
                timer.stop()
            return

        if timer is None:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(False)
            timer.timeout.connect(lambda name=monitor.name: self._trigger_periodic_monitor(name))
            self._periodic_timers[monitor.name] = timer

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
