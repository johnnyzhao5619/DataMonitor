# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: weijiazhao
# @File : mainFrame.py
# @Software: PyCharm


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog

from GUI_Windows_New import MainWindow
import apiMonitor
import configuration
import datetime
import logRecorder
import sys
import queue
from pathlib import Path
from typing import Optional

from monitoring.service import MonitorScheduler, ServerMonitorStrategy
from monitoring.state_machine import MonitorEvent


class toolsetWindow(QtWidgets.QMainWindow, MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 实例化创建状态栏
        self.status = self.statusBar()
        # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
        self.status.showMessage('>>初始化...', 4000)
        # 创建窗口标题
        self.setWindowTitle('Monitor Everything v0.2')
        self.switchButton.clicked.connect(self.start_monitor)
        self.configButton.clicked.connect(self.configuration)
        self.locationButton.clicked.connect(self.set_location)

        self.switch_status = True
        self.printf_queue = queue.Queue()
        self.time_zone = self._read_config_timezone()
        self._update_timezone_display()
        self.update_clock()
        self.scheduler: Optional[MonitorScheduler] = None

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

            self.switchButton.setText('关闭 Close')
            self.switch_status = False
        elif self.switch_status is False:
            if self.scheduler:
                self.scheduler.stop()
            QtWidgets.QApplication.quit()

    def configuration(self):
        return

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
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time = datetime.datetime.utcnow()
        current_time = utc_time + datetime.timedelta(hours=self.time_zone)
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))

        while True:
            try:
                message = self.printf_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.monitorBrowser.append(message)  # 在指定的区域显示提示信息
                self.cursot = self.monitorBrowser.textCursor()
                self.monitorBrowser.moveCursor(self.cursot.End)
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

    def _read_config_timezone(self):
        raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self):
        self.localTimeGroupBox.setTitle(f'本地时间 Local Time(时区 Time Zone: {self.time_zone})')

    def closeEvent(self, event):
        if self.scheduler:
            self.scheduler.stop()
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
