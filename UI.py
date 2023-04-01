# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 12:32 a.m.
# @Author: weijiazhao
# @File : UI.py
# @Software: PyCharm


import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
import datetime

class DynamicComponent(QWidget):
    def __init__(self):
        super().__init__()
        self.componentLayout = QVBoxLayout()
        self.setLayout(self.componentLayout)

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.monitorGroupBox = QGroupBox('API Monitor')
        self.monitorGroupBox.setFont(font)
        self.monitorGroupBox.setMinimumSize(QtCore.QSize(680, 120))
        self.monitorGroupBox.setMaximumSize(QtCore.QSize(680, 120))

        self.componentLayout.addWidget(self.monitorGroupBox)


        self.monitorLayout = QVBoxLayout()
        self.monitorGroupBox.setLayout(self.monitorLayout)


        self.intervalTittleLabel = QLabel('频率(s) Interval:')

        self.typeTittleLabel = QLabel('监控类型 Type:')
        self.urlTittleLabel = QLabel('地址 URL:')
        self.intervalLabel = QLabel('xxx')
        self.typeLabel = QLabel('xxx')
        self.urlLabel = QLabel('www.google.com')

        self.intervalTittleLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.typeTittleLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.urlTittleLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.intervalLabel.setMinimumSize(QtCore.QSize(200, 20))
        self.typeLabel.setMinimumSize(QtCore.QSize(200, 20))
        self.urlLabel.setMinimumSize(QtCore.QSize(200, 20))

        self.intervalTittleLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.typeTittleLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.urlTittleLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.intervalLabel.setMaximumSize(QtCore.QSize(200, 20))
        self.typeLabel.setMaximumSize(QtCore.QSize(200, 20))
        self.urlLabel.setMaximumSize(QtCore.QSize(200, 20))

        self.testTimeLabel = QLabel('2023-04-01 00:00:00')
        self.resultLabel = QLabel('通过')
        self.notesLabel = QLabel('xxx')
        self.testTimeLabel.setMinimumSize(QtCore.QSize(200, 20))
        self.resultLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.notesLabel.setMinimumSize(QtCore.QSize(200, 20))

        self.testTimeLabel.setMaximumSize(QtCore.QSize(200, 20))
        self.resultLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.notesLabel.setMaximumSize(QtCore.QSize(200, 20))



        self.iconLabel = QLabel('')
        self.iconLabel.setMinimumSize(QtCore.QSize(20, 20))
        self.iconLabel.setMaximumSize(QtCore.QSize(20, 20))
        self.iconLabel.setStyleSheet("background-color: Gray")


        # 第一行
        self.line1Layout = QHBoxLayout()
        self.line1Layout.addWidget(self.typeTittleLabel)
        self.line1Layout.addWidget(self.typeLabel)
        self.line1Layout.addStretch(1)
        self.monitorLayout.addLayout(self.line1Layout)


        # 第二行
        self.line2Layout = QHBoxLayout()
        self.line2Layout.addWidget(self.intervalTittleLabel)
        self.line2Layout.addWidget(self.intervalLabel)
        self.line2Layout.addStretch(1)
        self.monitorLayout.addLayout(self.line2Layout)

        # 第三行
        self.line3Layout = QHBoxLayout()
        self.line3Layout.addWidget(self.urlTittleLabel)
        self.line3Layout.addWidget(self.urlLabel)
        self.line3Layout.addStretch(1)
        self.monitorLayout.addLayout(self.line3Layout)

        #第四行
        self.line4Layout = QHBoxLayout()
        self.line4Layout.addWidget(self.iconLabel)
        self.line4Layout.addWidget(self.testTimeLabel)
        self.line4Layout.addWidget(self.resultLabel)
        self.line4Layout.addWidget(self.notesLabel)
        self.line4Layout.addStretch(1)
        self.monitorLayout.addLayout(self.line4Layout)

        # self.label = QLabel('This is a dynamic component')
        # self.componentLayout.addWidget(self.label)
        #
        # self.button = QPushButton('Click me!')
        # self.button.clicked.connect(self.on_button_click)
        # self.componentLayout.addWidget(self.button)

    def on_button_click(self):
        self.label.setText('You clicked the button!')

# 主窗口类
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        MainWindow.setMinimumSize(self, 720, 600)
        MainWindow.setMaximumSize(self, 720, 1000)

        # 创建时钟
        # 创建localTimeGroupBox
        self.localTimeGroupBox = QtWidgets.QGroupBox('本地时间 Local Time')
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
        self.utcTimeGroupBox = QtWidgets.QGroupBox('本地时间 Local Time')
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

        # 将时钟添加至窗口当中
        self.timeLayout = QHBoxLayout()
        self.timeLayout.addWidget(self.localTimeGroupBox)
        self.timeLayout.addWidget(self.utcTimeGroupBox)
        self.mainLayout.addLayout(self.timeLayout)


        # # 创建按钮
        # self.button = QPushButton('Load dynamic component')
        # self.button.clicked.connect(self.load_dynamic_component)
        # self.mainLayout.addWidget(self.button)


        # 保证在最上面
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayout.addItem(spacerItem)


    def load_dynamic_component(self):
        self.dynamic_component = DynamicComponent()
        self.mainLayout.addWidget(self.dynamic_component)

    def update_clock(self):
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time = datetime.datetime.utcnow()
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))