# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 12:32 a.m.
# @Author: weijiazhao
# @File : GUI_Mac.py

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
import configuration

# time_zone = configuration.get_timezone()


# 主窗口类
class MainWindow(object):

    def setupUi(self, Monitor):
        # def __init__(self):
        global switch

        Monitor.setMaximumSize(QtCore.QSize(890, 580))
        Monitor.setMinimumSize(QtCore.QSize(890, 580))

        self.MonitorLayout = QtWidgets.QWidget(Monitor)
        self.MonitorLayout.setGeometry(QtCore.QRect(0, 0, 890, 580))
        self.mainLayout = QtWidgets.QVBoxLayout(self.MonitorLayout)

        # 创建按钮
        self.buttonLayout = QHBoxLayout(Monitor)

        self.switchButton = QPushButton('Monitor')
        self.switchButton.setMaximumSize(QtCore.QSize(180, 40))
        self.switchButton.setMinimumSize(QtCore.QSize(180, 40))

        self.configButton = QPushButton('Configuration')
        self.configButton.setMaximumSize(QtCore.QSize(200, 40))
        self.configButton.setMinimumSize(QtCore.QSize(200, 40))

        self.locationButton = QPushButton('Time Zone')
        self.locationButton.setMaximumSize(QtCore.QSize(200, 40))
        self.locationButton.setMinimumSize(QtCore.QSize(200, 40))

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(True)
        self.switchButton.setFont(font)
        self.configButton.setFont(font)
        self.locationButton.setFont(font)

        # 将按钮添加至buttonlayout当中
        self.buttonLayout.addWidget(self.switchButton)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.configButton)
        self.buttonLayout.addWidget(self.locationButton)

        # 创建时钟
        # 创建localTimeGroupBox
        self.localTimeGroupBox = QtWidgets.QGroupBox(
            f'Local Time(Time Zone: {configuration.get_timezone()})')
        # self.localTimeGroupBox.setGeometry(QtCore.QRect(10, 70, 340, 80))

        # 为GroupBox创建设置布局
        self.localTimeLayout = QVBoxLayout()
        self.localTimeGroupBox.setLayout(self.localTimeLayout)
        self.localTimeGroupBox.setMinimumSize(QtCore.QSize(420, 80))
        self.localTimeGroupBox.setMaximumSize(QtCore.QSize(420, 80))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setWeight(20)
        font.setBold(True)
        self.localTimeGroupBox.setFont(font)
        # 创建LocalTimeLabel
        self.localTimeLabel = QtWidgets.QLabel(self.localTimeGroupBox)
        self.localTimeLabel.setMinimumSize(QtCore.QSize(420, 40))
        self.localTimeLabel.setMaximumSize(QtCore.QSize(420, 40))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(40)
        self.localTimeLabel.setFont(font)
        self.localTimeLayout.addWidget(self.localTimeLabel)

        # 创建UTCTimeGroupBox
        self.utcTimeGroupBox = QtWidgets.QGroupBox('UTC Time')
        # self.utcTimeGroupBox.setGeometry(QtCore.QRect(350, 70, 340, 80))

        # 为GroupBox创建设置布局
        self.utcTimeLayout = QVBoxLayout()
        self.utcTimeGroupBox.setLayout(self.utcTimeLayout)
        self.utcTimeGroupBox.setMinimumSize(QtCore.QSize(420, 80))
        self.utcTimeGroupBox.setMaximumSize(QtCore.QSize(420, 80))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setWeight(20)
        font.setBold(True)
        self.utcTimeGroupBox.setFont(font)

        # 创建utcTimeLabel
        self.utcTimeLabel = QtWidgets.QLabel(self.utcTimeGroupBox)
        self.utcTimeLabel.setMinimumSize(QtCore.QSize(420, 40))
        self.utcTimeLabel.setMaximumSize(QtCore.QSize(420, 40))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(40)
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
        self.monitorBrowser.setGeometry(QtCore.QRect(10, 10, 850, 320))

        self.monitorBrowser.setMinimumSize(QtCore.QSize(850, 350))
        self.monitorBrowser.setMaximumSize(QtCore.QSize(850, 350))

        self.mainLayout.addLayout(self.buttonLayout)

        # 将时钟添加至窗口当中
        self.timeLayout = QHBoxLayout()
        self.timeLayout.addWidget(self.localTimeGroupBox)
        self.timeLayout.addWidget(self.utcTimeGroupBox)
        self.mainLayout.addLayout(self.timeLayout)

        # 添加监控窗口
        self.mainLayout.addWidget(self.logLine)

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        self.monitorBrowser.setFont(font)
        self.mainLayout.addWidget(self.monitorBrowser)
        self.mainLayout.addStretch(1)
