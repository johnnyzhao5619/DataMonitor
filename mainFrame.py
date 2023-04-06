# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: weijiazhao
# @File : mainFrame.py
# @Software: PyCharm
import os

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QInputDialog

from UI import MainWindow
import apiMonitor
import sendEmail
import time
import threading
import configuration
import datetime
import sys
import logRecorder


switch_status = True
time_zone = int(configuration.get_timezone())
printf = []

class toolsetWindow(QtWidgets.QMainWindow, MainWindow):
    global switch_status
    global time_zone
    global printf
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 实例化创建状态栏
        self.status = self.statusBar()
        # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
        self.status.showMessage('>>初始化...', 4000)
        # 创建窗口标题
        self.setWindowTitle('API Monitor v0.1')
        self.switchButton.clicked.connect(self.start_monitor)
        self.configButton.clicked.connect(self.configuration)
        self.locationButton.clicked.connect(self.set_location)

    def start_monitor(self):
        global switch_status
        if switch_status == True:
            monitorList = configuration.read_monitor_list()
            # self.printf(f"目前读取到{len(monitorList)}个监控项，分别是：")
            printf.append(f"目前读取到{len(monitorList)}个监控项，分别是：")
            logRecorder.record("Start Monitor", f"目前读取到{len(monitorList)}个监控项")
            for i in range(len(monitorList)):
                name = monitorList[i]['name']
                url = monitorList[i]['url']
                interval = monitorList[i]['interval']
                mtype = monitorList[i]['type']
                print("name:", name)

                # Log和输出————————————————————————————————————————————————————————————————————————
                # self.printf(f"{i+1}. {name} --- 类型: {mtype} --- 地址: {url} --- 周期: {interval}秒")
                printf.append(f"{i+1}. {name} --- 类型: {mtype} --- 地址: {url} --- 周期: {interval}秒")
                # 记录Log日志
                logRecorder.record("读取配置 Read Configuration", f"{i+1}.{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒\n")

            self.run_with_threads(len(monitorList), monitorList)

            self.switchButton.setText('关闭 Close')
            switch_status = False
        elif switch_status == False:
            sys.exit()

    def configuration(self):
        return

    def set_location(self):
        global time_zone
        # 后面四个数字的作用依次是 初始值 最小值 最大值 步幅
        time_zone, ok = QInputDialog.getInt(self, "输入时区", "请输入所在时区(整数):", time_zone, -12, 14, 1)
        self.localTimeGroupBox.setTitle(f'本地时间 Local Time(时区 Time Zone: {time_zone})')
        # self.echo(time_zone)

    def update_clock(self):
        global time_zone
        global printf
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time = datetime.datetime.utcnow()
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=time_zone)
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))

        while len(printf) > 0:
            for i in printf:
                self.monitorBrowser.append(i)  # 在指定的区域显示提示信息
                self.cursot = self.monitorBrowser.textCursor()
                self.monitorBrowser.moveCursor(self.cursot.End)
            printf.clear()
            QtWidgets.QApplication.processEvents()


    def perform_task(self, url, type, email):
        # 发送请求
        if type == "GET":
            result = apiMonitor.monitor_get(url)
        elif type == "POST":
            result = apiMonitor.monitor_post(url, "1")
        elif type == "SERVER":
            result = apiMonitor.monitor_server(url)
        return result

    # 格式化url
    def parse_network_address(self, address):
        """
        Parses a network address string in the format "http(s)://url:port/suffix" and returns a list
        containing the URL, port, and suffix.
        """
        if address.startswith("http://"):
            url_port_suffix = address[len("http://"):]
        elif address.startswith("https://"):
            url_port_suffix = address[len("https://"):]
        else:
            url_port_suffix = address

        print("url_port_suffix:", url_port_suffix)

        if '/' in url_port_suffix:
            url_port, suffix = url_port_suffix.split('/', 1)
        else:
            url_port = url_port_suffix
            suffix = ''

        if ':' in url_port:
            url, port = url_port.split(':')
            port = int(port)
        else:
            url = url_port
            port = 80

        return [url, int(port), suffix]

    # 周期性运行
    def run_periodically(self, monitorInfo):
        global time_zone
        global printf
        i = 1
        lastStatus = True
        while True:
            # 获取配置信息
            name = monitorInfo['name']
            url = monitorInfo['url']
            mtype = monitorInfo['type']
            interval = int(monitorInfo['interval'])
            email = monitorInfo['email']

            # 格式化url
            url = self.parse_network_address(url)

            # 触发状态监控监控流程
            result = self.perform_task(url, mtype, email)
            timenow = datetime.datetime.utcnow() + datetime.timedelta(hours=time_zone)

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
                printf.append(f"时间：{timenow} --> 状态：{name}服务正常")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务正常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '正常'], name)

            elif responseCode == 2:
                sendEmail.send_email(f"{timenow}: {name} Server Outage Recovery!", f"{name}服务已恢复\n恢复时间：{timenow}\n")
                print(f"\n第{i}次：{timenow}状态 --> {name}服务恢复")
                # Log和输出————————————————————————————————————————————————————————————————————————
                printf.append(f"时间：{timenow} --> 状态：{name}服务恢复")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务恢复\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '恢复'], name)

            elif responseCode == 3:
                sendEmail.send_email(f"{timenow}: {name} Server Outage Recovery!", f"{name}服务异常\n发生时间：{timenow}")
                print(f"\n第{i}次：{timenow}状态 --> {name}服务异常")
                # Log和输出————————————————————————————————————————————————————————————————————————
                printf.append(f"时间：{timenow} --> 状态：{name}服务异常")
                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务异常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '异常'], name)

            elif responseCode == 4:
                print(f"\n第{i}次：{timenow}状态 --> {name}服务持续异常")
                # Log和输出————————————————————————————————————————————————————————————————————————
                # self.printf(f"时间：{timenow} --> 状态：{name}服务持续异常")
                printf.append_message(f"时间：{timenow} --> 状态：{name}服务持续异常")

                # 记录Log日志
                logRecorder.record(f"{name} --- 类型 Type: {mtype} --- 地址 url: {url} --- 周期 Interval: {interval}秒", f">>>{timenow}: {name}服务持续异常\n")
                logRecorder.saveToFile([timenow, name, mtype, url, interval, responseCode, '持续异常'], name)

            if responseCode == 1 or responseCode == 2:
                # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
                self.status.showMessage('运行中...')
            else:
                # 将提示信息显示在状态栏中showMessage（‘提示信息’，显示时间（单位毫秒））
                self.status.showMessage(f'{name}服务异常')
            print(f"\n等待{interval}秒")
            i += 1
            lastStatus = result
            time.sleep(interval)

    # 根据需求，为每个监控项启动独立的线程
    def run_with_threads(self, num_threads:int, monitorList:list):
        for i in range(num_threads):
            monitorInfo = monitorList[i]
            t = threading.Thread(name=monitorInfo['name'], target=self.run_periodically, args=(monitorInfo,))
            # t = threading.Thread(target=super().run_periodically, args=(monitorInfo,))
            t.start()

            # threadList.append(t)
        # for t in threadList:
        #     t.setDaemon(True)
        #     t.start()

    # 写入文件
    def saveToFile(dataString, type):
        # 根据UTC时间，换算成中国区域时间

        folder = os.path.expanduser("~/Downloads/Toolset_Log")
        if not os.path.exists(folder):  # 判断是否存在文件夹如果不存在则创建为文件夹
            os.makedirs(folder)  # makedirs 创建文件时如果路径不存在会创建这个路径

        nowDateTime = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        nowDate = nowDateTime.strftime("%Y%m%d")
        # 单独存储至文件
        csv = open(f'{folder}/BSMRelay_{type}_{nowDate}.txt', 'w', encoding='utf-8')
        csv.write(dataString)
        csv.close()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = toolsetWindow()
    mainWindow.show()
    sys.exit(app.exec_())