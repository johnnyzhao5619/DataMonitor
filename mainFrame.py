from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.main_window import MainWindowUI
import apiMonitor
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import datetime
import logRecorder
import sendEmail
import sys
import queue
import time
from pathlib import Path
from typing import Optional

from monitoring.service import MonitorScheduler, ServerMonitorStrategy
from monitoring.state_machine import MonitorEvent

NOTIFICATION_STATES = {
    "normal": {
        "code": 1,
        "status_label": "服务正常",
        "status_text": "正常",
        "status_action": "正常",
        "event_description": "监控检测到服务保持正常状态",
        "time_label": "检测时间",
        "mail_event": None,
    },
    "recovery": {
        "code": 2,
        "status_label": "服务恢复",
        "status_text": "恢复",
        "status_action": "恢复",
        "event_description": "监控检测到服务恢复至正常状态",
        "time_label": "恢复时间",
        "mail_event": "recovery",
    },
    "alert": {
        "code": 3,
        "status_label": "服务异常",
        "status_text": "异常",
        "status_action": "告警",
        "event_description": "监控检测到服务不可达",
        "time_label": "发生时间",
        "mail_event": "alert",
    },
    "ongoing": {
        "code": 4,
        "status_label": "服务持续异常",
        "status_text": "持续异常",
        "status_action": "告警",
        "event_description": "监控检测到服务持续处于异常状态",
        "time_label": "检测时间",
        "mail_event": None,
    },
}


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
        i = 1
        lastStatus = True
        while True:
            # 获取配置信息
            name = monitorInfo['name']
            url = monitorInfo['url']
            raw_type = monitorInfo.get('type')
            if isinstance(raw_type, str):
                mtype = raw_type.strip().upper()
            elif raw_type is None:
                mtype = ""
            else:
                self._log_unsupported_type(raw_type, url, name=name)
                return

            if mtype not in SUPPORTED_MONITOR_TYPES:
                self._log_unsupported_type(mtype or raw_type, url, name=name)
                return
            interval = int(monitorInfo['interval'])
            email = monitorInfo.get('email')
            recipients = email.strip() if isinstance(email, str) else None
            if not recipients:
                recipients = None

            # 仅在SERVER类型下解析地址
            parsed_address = None
            if mtype == "SERVER":
                parsed_address = self.parse_network_address(url)

            # 触发状态监控监控流程
            result = self.perform_task(
                url,
                parsed_address,
                mtype,
                email,
                payload=monitorInfo.get('payload'),
                headers=monitorInfo.get('headers'),
            )
            timenow = datetime.datetime.utcnow() + datetime.timedelta(hours=self.time_zone)
            timestamp_text = timenow.strftime('%Y-%m-%d %H:%M:%S')
            interval_value = int(interval)

            is_success = bool(result)
            state_changed = is_success != bool(lastStatus)

            if is_success and not state_changed:
                state_key = "normal"
            elif is_success and state_changed:
                state_key = "recovery"
            elif not is_success and state_changed:
                state_key = "alert"
            else:
                state_key = "ongoing"

            profile = NOTIFICATION_STATES[state_key]
            context = {
                "service_name": name,
                "monitor_type": mtype,
                "url": url,
                "interval": interval_value,
                "status_code": profile["code"],
                "status_key": state_key,
                "status_label": profile["status_label"],
                "status_text": profile["status_text"],
                "status_action": profile["status_action"],
                "event_description": profile["event_description"],
                "time_label": profile["time_label"],
                "event_timestamp": timestamp_text,
            }

            if profile["mail_event"]:
                subject, body = sendEmail.render_email(profile["mail_event"], context)
                sendEmail.send_email(subject, body, recipients=recipients)

            ui_message = configuration.render_template("ui", "status_line", context)
            print(f"\n第{i}次：{ui_message}")
            self.printf_queue.put(ui_message)

            action_line = configuration.render_template("log", "action_line", context)
            detail_line = configuration.render_template("log", "detail_line", context)
            logRecorder.record(action_line, detail_line)
            logRecorder.saveToFile(
                [
                    timestamp_text,
                    name,
                    mtype,
                    url,
                    interval_value,
                    profile["code"],
                    profile["status_text"],
                ],
                name,
            )

            if profile["code"] in (1, 2):
                self.status.showMessage('>>>运行中...')
            else:
                self.status.showMessage(f'{name}{profile["status_label"]}')
            print(f"\n等待{interval_value}秒")
            i += 1
            lastStatus = is_success
            time.sleep(interval_value)

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
