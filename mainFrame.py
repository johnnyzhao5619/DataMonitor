# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: weijiazhao
# @File : mainFrame.py
# @Software: PyCharm


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog

from GUI_Windows_New import MainWindow
import apiMonitor
import sendEmail
import time
import threading
import configuration
import datetime
import sys
import logRecorder
import queue
from pathlib import Path


SUPPORTED_MONITOR_TYPES = {"GET", "POST", "SERVER"}

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

    def start_monitor(self):
        if self.switch_status is True:
            monitorList = configuration.read_monitor_list()
            # self.printf(f"目前读取到{len(monitorList)}个监控项，分别是：")
            self.printf_queue.put(f"目前读取到{len(monitorList)}个监控项，分别是：")
            logRecorder.record("Start Monitor", f"目前读取到{len(monitorList)}个监控项")
            for i in range(len(monitorList)):
                name = monitorList[i]['name']
                url = monitorList[i]['url']
                interval = monitorList[i]['interval']
                mtype = monitorList[i]['type']
                print("name:", name)

                # Log和输出————————————————————————————————————————————————————————————————————————
                # self.printf(f"{i+1}. {name} --- 类型: {mtype} --- 地址: {url} --- 周期: {interval}秒")
                self.printf_queue.put(f"{i+1}. {name} --- 类型: {mtype} --- 地址: {url} --- 周期: {interval}秒")
                # 记录Log日志
                logRecorder.record("读取配置 Read Configuration", f"{i+1}.{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒\n")

            self.run_with_threads(len(monitorList), monitorList)

            self.switchButton.setText('关闭 Close')
            self.switch_status = False
        elif self.switch_status is False:
            sys.exit()

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


    def perform_task(self, url, parsed_address, type, email, payload=None, *, headers=None):
        # 发送请求
        if type == "GET":
            result = apiMonitor.monitor_get(url)
        elif type == "POST":
            result = apiMonitor.monitor_post(url, payload, headers=headers)
        elif type == "SERVER":
            if parsed_address is None:
                parsed_address = self.parse_network_address(url)
            result = apiMonitor.monitor_server(parsed_address)
        else:
            self._log_unsupported_type(type, url)
            return False
        return result

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

    def _read_config_timezone(self):
        raw_value = configuration.get_timezone()
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return 0

    def _update_timezone_display(self):
        self.localTimeGroupBox.setTitle(f'本地时间 Local Time(时区 Time Zone: {self.time_zone})')

    # 根据需求，为每个监控项启动独立的线程
    def run_with_threads(self, num_threads:int, monitorList:list):
        for i in range(num_threads):
            monitorInfo = monitorList[i]
            t = threading.Thread(name=monitorInfo['name'], target=self.run_periodically, args=(monitorInfo,))
            # t = threading.Thread(target=super().run_periodically, args=(monitorInfo,))
            t.setDaemon(True)
            t.start()


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
