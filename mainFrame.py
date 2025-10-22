from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.main_window import MainWindowUI
import apiMonitor
import sendEmail
import time
import threading
import configuration
from configuration import SUPPORTED_MONITOR_TYPES
import datetime
import sys
import logRecorder
import queue
from pathlib import Path


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

    def start_monitor(self):
        if self.switch_status is True:
            monitorList = configuration.read_monitor_list()
            self.printf_queue.put(f"目前读取到{len(monitorList)}个监控项，分别是：")
            logRecorder.record("Start Monitor", f"目前读取到{len(monitorList)}个监控项")
            for i in range(len(monitorList)):
                name = monitorList[i]['name']
                url = monitorList[i]['url']
                interval = monitorList[i]['interval']
                mtype = monitorList[i]['type']
                print("name:", name)

                self.printf_queue.put(f"{i+1}. {name} --- 类型: {mtype} --- 地址: {url} --- 周期: {interval}秒")
                logRecorder.record("读取配置 Read Configuration", f"{i+1}.{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒\n")

            self.run_with_threads(len(monitorList), monitorList)

            self.ui.show_monitor_page()
            self.ui.switchButton.setText('关闭 Close')
            self.switch_status = False
        elif self.switch_status is False:
            sys.exit()

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

            # 判断结果
            # 当状态正常，且跟上一次状态一致时，无操作，等待下一次
            if result == True and result == lastStatus:
                responseCode = 1  # 服务正常
            # 当状态正常，且跟上一次状态不一致时，发送数据恢复邮件
            elif result == True and result != lastStatus:
                responseCode = 2  # 服务恢复
            # 当状态不正常，且跟上一次状态不一致时，发送数据中断告警邮件
            elif result == False and result != lastStatus:
                responseCode = 3  # 服务异常
            # 当状态不正常，且跟上一次状态一致时，数据持续异常
            elif result == False and result == lastStatus:
                responseCode = 4  # 服务持续异常

            # 给予结果进行处理
            if responseCode == 1:
                print(f"\n第{i}次：{timenow} --> 状态：{name}服务正常")
                # Log和输出————————————————————————————————————————————————————————————————————————
                self.printf_queue.put(f"时间：{timenow} --> 状态：{name}服务正常")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务正常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '正常'], name)

            elif responseCode == 2:
                subject, body = sendEmail.build_outage_recovery_message(name, timenow)
                sendEmail.send_email(subject, body, recipients=recipients)
                print(f"\n第{i}次：{timenow}状态 --> {name}服务恢复")
                # Log和输出————————————————————————————————————————————————————————————————————————
                self.printf_queue.put(f"时间：{timenow} --> 状态：{name}服务恢复")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务恢复\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '恢复'], name)

            elif responseCode == 3:
                subject, body = sendEmail.build_outage_alert_message(name, timenow)
                sendEmail.send_email(subject, body, recipients=recipients)
                print(f"\n第{i}次：{timenow}状态 --> {name}服务异常")
                # Log和输出————————————————————————————————————————————————————————————————————————
                self.printf_queue.put(f"时间：{timenow} --> 状态：{name}服务异常")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务异常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '异常'], name)

            elif responseCode == 4:
                print(f"\n第{i}次：{timenow}状态 --> {name}服务持续异常")
                # Log和输出————————————————————————————————————————————————————————————————————————
                # self.printf(f"时间：{timenow} --> 状态：{name}服务持续异常")
                self.printf_queue.put(f"时间：{timenow} --> 状态：{name}服务持续异常")

                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务持续异常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '持续异常'], name)

            if responseCode == 1 or responseCode == 2:
                # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
                self.status.showMessage('>>>运行中...')
            else:
                # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
                self.status.showMessage(f'{name}服务异常')
            print(f"\n等待{interval}秒")
            i += 1
            lastStatus = result
            time.sleep(interval)

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
