# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 12:32 a.m.
# @Author: weijiazhao
# @File : UI.py
# @Software: PyCharm


import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QApplication, \
    QInputDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
# import datetime
import configuration
# import mainFrame
#
# switch = True
# time_zone = 8
time_zone = configuration.get_timezone()



# 主窗口类
class MainWindow(object):
    def setupUi(self, Monitor):
    # def __init__(self):
        global switch
        global time_zone

        Monitor.setMinimumSize(QtCore.QSize(720, 500))
        Monitor.setMaximumSize(QtCore.QSize(720, 1000))

        self.MonitorLayout = QtWidgets.QWidget(Monitor)
        self.MonitorLayout.setGeometry(QtCore.QRect(0, 0, 720, 500))
        self.mainLayout = QtWidgets.QVBoxLayout(self.MonitorLayout)


        # 创建按钮
        self.buttonLayout = QHBoxLayout(Monitor)

        self.switchButton = QPushButton('监控 Monitor')
        self.switchButton.setMaximumSize(QtCore.QSize(120, 35))
        self.switchButton.setMinimumSize(QtCore.QSize(120, 35))

        self.configButton = QPushButton('配置 Configuration')
        self.configButton.setMaximumSize(QtCore.QSize(150, 35))
        self.configButton.setMinimumSize(QtCore.QSize(150, 35))

        self.locationButton = QPushButton('时区 Time Zone')
        self.locationButton.setMaximumSize(QtCore.QSize(150, 35))
        self.locationButton.setMinimumSize(QtCore.QSize(150, 35))

        # 将按钮添加至buttonlayout当中
        self.buttonLayout.addWidget(self.switchButton)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.configButton)
        self.buttonLayout.addWidget(self.locationButton)



        # 创建时钟
        # 创建localTimeGroupBox
        self.localTimeGroupBox = QtWidgets.QGroupBox(f'本地时间 Local Time(时区 Time Zone: {time_zone})')
        # self.localTimeGroupBox.setGeometry(QtCore.QRect(10, 70, 340, 80))

        # 为GroupBox创建设置布局
        self.localTimeLayout = QVBoxLayout()
        self.localTimeGroupBox.setLayout(self.localTimeLayout)
        self.localTimeGroupBox.setMinimumSize(QtCore.QSize(340, 80))
        self.localTimeGroupBox.setMaximumSize(QtCore.QSize(340, 80))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.localTimeGroupBox.setFont(font)
        # 创建LocalTimeLabel
        self.localTimeLabel = QtWidgets.QLabel(self.localTimeGroupBox)
        self.localTimeLabel.setMaximumSize(QtCore.QSize(320, 50))
        self.localTimeLabel.setMaximumSize(QtCore.QSize(320, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(26)
        font.setBold(True)
        font.setWeight(75)
        self.localTimeLabel.setFont(font)
        self.localTimeLayout.addWidget(self.localTimeLabel)

        # 创建UTCTimeGroupBox
        self.utcTimeGroupBox = QtWidgets.QGroupBox('UTC时间 UTC Time')
        self.utcTimeGroupBox.setGeometry(QtCore.QRect(350, 70, 340, 80))

        # 为GroupBox创建设置布局
        self.utcTimeLayout = QVBoxLayout()
        self.utcTimeGroupBox.setLayout(self.utcTimeLayout)
        self.utcTimeGroupBox.setMinimumSize(QtCore.QSize(340, 80))
        self.utcTimeGroupBox.setMaximumSize(QtCore.QSize(340, 80))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.utcTimeGroupBox.setFont(font)

        # 创建utcTimeLabel
        self.utcTimeLabel = QtWidgets.QLabel(self.utcTimeGroupBox)
        self.utcTimeLabel.setMaximumSize(QtCore.QSize(320, 50))
        self.utcTimeLabel.setMaximumSize(QtCore.QSize(320, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(26)
        font.setBold(True)
        font.setWeight(75)
        self.utcTimeLabel.setFont(font)
        self.utcTimeLayout.addWidget(self.utcTimeLabel)

        # create the timer to update the clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(100)

        # 创建监控窗口
        self.logLine = QtWidgets.QFrame()
        self.logLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.logLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.monitorBrowser = QtWidgets.QTextBrowser()
        self.monitorBrowser.setGeometry(QtCore.QRect(10, 10, 700, 300))

        self.monitorBrowser.setMinimumSize(QtCore.QSize(700, 300))
        self.monitorBrowser.setMaximumSize(QtCore.QSize(700, 300))

        self.mainLayout.addLayout(self.buttonLayout)

        # 将时钟添加至窗口当中
        self.timeLayout = QHBoxLayout()
        self.timeLayout.addWidget(self.localTimeGroupBox)
        self.timeLayout.addWidget(self.utcTimeGroupBox)
        self.mainLayout.addLayout(self.timeLayout)

        # 添加监控窗口
        self.mainLayout.addWidget(self.logLine)
        self.mainLayout.addWidget(self.monitorBrowser)

        self.mainLayout.addStretch(1)



    # def start_monitor(self, status):
    #     global switch
    #     if status == True:
    #         monitorList = configuration.read_monitor_list()
    #         for i in range(len(monitorList)):
    #             name = monitorList[i]['name']
    #             print("name:", name)
    #         mainFrame.run_with_threads(len(monitorList), monitorList)
    #         self.button.setText('关闭 Close')
    #         switch = False
    #     elif status == False:
    #         sys.exit()
    #
    # def configuration(self):
    #     return
    #
    # def set_location(self):
    #     global time_zone
    #     # 后面四个数字的作用依次是 初始值 最小值 最大值 步幅
    #     time_zone, ok = QInputDialog.getInt(self, "输入时区", "请输入所在时区\n\n请输入整数:", time_zone, -12, 14, 1)
    #     self.localTimeGroupBox.setTitle(f'本地时间 Local Time(时区 Time Zone: {time_zone})')
    #     # self.echo(time_zone)
    #
    #
    # def update_clock(self):
    #     global time_zone
    #     # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
    #     utc_time = datetime.datetime.utcnow()
    #     current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=time_zone)
    #     self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
    #     self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))




# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.setGeometry(100, 100, 720, 600)  # set default window size to 200x200
#     window.show()
#     sys.exit(app.exec_())