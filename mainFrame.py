# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:22 p.m.
# @Author: weijiazhao
# @File : mainFrame.py
# @Software: PyCharm
from PyQt5.QtWidgets import QApplication

import apiMonitor
import sendEmail
import time
import threading
import configuration
import datetime
import UI
import sys


def perform_task(url, type, email):
    # 发送请求
    if type == "GET":
        result = apiMonitor.monitor_get(url)
    elif type == "POST":
        result = apiMonitor.monitor_post(url, "1")
    elif type == "SERVER":
        result = apiMonitor.monitor_server(url)
    return result

# 格式化url
def parse_network_address(address):
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
def run_periodically(monitorInfo):
    i = 1
    lastStatus = True
    while True:
        # 获取配置信息
        name = monitorInfo['name']
        url = monitorInfo['url']
        type = monitorInfo['type']
        interval = int(monitorInfo['interval'])
        email = monitorInfo['email']

        # 格式化url
        url = parse_network_address(url)

        # 触发状态监控监控流程
        result = perform_task(url, type, email)
        timenow = datetime.datetime.utcnow() + datetime.timedelta(hours=8)

        # 判断结果
        # 当状态正常，且跟上一次状态一致时，无操作，等待下一次
        if result == True and result == lastStatus:
            print(f"\n第{i}次：{timenow}状态 --> {name}服务正常")

        # 当状态正常，且跟上一次状态不一致时，发送数据恢复邮件
        elif result == True and result != lastStatus:
            sendEmail.send_email(f"{timenow}: {name} Server Outage Recovery!", f"{name}服务已恢复\n恢复时间：{timenow}\n")
            print(f"\n第{i}次：{timenow}状态 --> {name}服务恢复")

        # 当状态不正常，且跟上一次状态一致时，数据持续异常
        elif result == False and result == lastStatus:
            print(f"\n第{i}次：{timenow}状态 --> {name}服务持续异常")

        # 当状态不正常，且跟上一次状态不一致时，发送数据中断告警邮件
        elif result == False and result != lastStatus:
            sendEmail.send_email(f"{timenow}: {name} Server Outage Recovery!", f"{name}服务异常\n发生时间：{timenow}")
            print(f"\n第{i}次：{timenow}状态 --> {name}服务异常")

        print(f"\n等待{interval}秒")
        i += 1
        lastStatus = result
        time.sleep(interval)

# 根据需求，为每个监控项启动独立的线程
def run_with_threads(num_threads, monitorList):
    for i in range(num_threads):
        monitorInfo = monitorList[i]
        t = threading.Thread(target=run_periodically, args=(monitorInfo,))
        t.start()


if __name__ == "__main__":
    monitorList = configuration.read_monitor_list()
    for i in range(len(monitorList)):
        name = monitorList[i]['name']
        print("name:", name)


    # UI.MainWindow.load_dynamic_component()
    #
    # app = QApplication(sys.argv)
    # window = UI.MainWindow()
    # window.setGeometry(100, 100, 720, 600)  # set default window size to 200x200
    # window.show()
    # sys.exit(app.exec_())

    run_with_threads(len(monitorList), monitorList)


