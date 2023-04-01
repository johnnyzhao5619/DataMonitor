# -*- codeing = utf-8 -*-
# @Time : 2023-03-30 2:26 a.m.
# @Author: weijiazhao
# @File : mainTest.py
# @Software: PyCharm

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QDate, QTime, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QScrollArea


import sys
import os
import shutil
import fnmatch
import datetime
import time

import GUI
from GUI import Ui_MainWindow
import test02


class mainTest(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        global nowDate
        global nowTime
        self.setupUi(self)
        # create the timer to update the clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(100)
        self.verticalLayout.addWidget(self.addMonitorGroup("1"))

    def update_clock(self):
        # current_time = QTime.currentTime().toString("Y-M-D hh:mm:ss")
        utc_time = datetime.datetime.utcnow()
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        self.localTimeLabel.setText(current_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.utcTimeLabel.setText(utc_time.strftime('%Y-%m-%d %H:%M:%S'))






if __name__ == '__main__':
    # 根据UTC时间，换算成中国区域时间
    nowDateTime = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    nowDate = QDate(int(nowDateTime.strftime("%Y")), int(nowDateTime.strftime("%m")), int(nowDateTime.strftime("%d")))
    nowTime = QTime(int(nowDateTime.strftime("%H")), int(nowDateTime.strftime("%M")), int(nowDateTime.strftime("%S")), 000)

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = mainTest()
    mainWindow.show()
    sys.exit(app.exec_())
