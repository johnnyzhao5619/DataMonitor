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
        return result

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
            mtype = monitorInfo['type']
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

    def _read_config_timezone(self):
        try:
            return int(configuration.get_timezone())
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
