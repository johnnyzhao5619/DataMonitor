# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 12:32 a.m.
# @Author: John Zhao
# @File : GUI_windows_v2.py

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer


class MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 500)
        MainWindow.setMaximumSize(QtCore.QSize(700, 500))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.switchButton = QtWidgets.QPushButton(self.centralwidget)
        self.switchButton.setGeometry(QtCore.QRect(10, 10, 120, 35))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.switchButton.sizePolicy().hasHeightForWidth())
        self.switchButton.setSizePolicy(sizePolicy)
        self.switchButton.setMaximumSize(QtCore.QSize(120, 35))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.switchButton.setFont(font)
        self.switchButton.setObjectName("switchButton")
        self.configButton = QtWidgets.QPushButton(self.centralwidget)
        self.configButton.setGeometry(QtCore.QRect(330, 10, 180, 35))
        self.configButton.setMaximumSize(QtCore.QSize(180, 35))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.configButton.setFont(font)
        self.configButton.setObjectName("configButton")
        self.locationButton = QtWidgets.QPushButton(self.centralwidget)
        self.locationButton.setGeometry(QtCore.QRect(510, 10, 180, 35))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.locationButton.sizePolicy().hasHeightForWidth())
        self.locationButton.setSizePolicy(sizePolicy)
        self.locationButton.setMaximumSize(QtCore.QSize(180, 35))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.locationButton.setFont(font)
        self.locationButton.setObjectName("locationButton")
        self.localTimeGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.localTimeGroupBox.setGeometry(QtCore.QRect(10, 50, 335, 60))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.localTimeGroupBox.sizePolicy().hasHeightForWidth())
        self.localTimeGroupBox.setSizePolicy(sizePolicy)
        self.localTimeGroupBox.setMaximumSize(QtCore.QSize(335, 60))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.localTimeGroupBox.setFont(font)
        self.localTimeGroupBox.setObjectName("localTimeGroupBox")
        self.localTimeLabel = QtWidgets.QLabel(self.localTimeGroupBox)
        self.localTimeLabel.setGeometry(QtCore.QRect(20, 20, 335, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.localTimeLabel.sizePolicy().hasHeightForWidth())
        self.localTimeLabel.setSizePolicy(sizePolicy)
        self.localTimeLabel.setMaximumSize(QtCore.QSize(335, 30))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.localTimeLabel.setFont(font)
        self.localTimeLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.localTimeLabel.setObjectName("localTimeLabel")
        self.utcTimeGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.utcTimeGroupBox.setGeometry(QtCore.QRect(355, 50, 335, 60))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.utcTimeGroupBox.sizePolicy().hasHeightForWidth())
        self.utcTimeGroupBox.setSizePolicy(sizePolicy)
        self.utcTimeGroupBox.setMaximumSize(QtCore.QSize(335, 60))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.utcTimeGroupBox.setFont(font)
        self.utcTimeGroupBox.setObjectName("utcTimeGroupBox")
        self.utcTimeLabel = QtWidgets.QLabel(self.utcTimeGroupBox)
        self.utcTimeLabel.setGeometry(QtCore.QRect(20, 20, 335, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.utcTimeLabel.sizePolicy().hasHeightForWidth())
        self.utcTimeLabel.setSizePolicy(sizePolicy)
        self.utcTimeLabel.setMaximumSize(QtCore.QSize(335, 30))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.utcTimeLabel.setFont(font)
        self.utcTimeLabel.setObjectName("utcTimeLabel")
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(10, 110, 680, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setMaximumSize(QtCore.QSize(680, 20))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.monitorBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.monitorBrowser.setGeometry(QtCore.QRect(10, 130, 680, 320))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.monitorBrowser.setFont(font)
        self.monitorBrowser.setObjectName("monitorBrowser")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        # create the timer to update the clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(100)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.switchButton.setText(_translate("MainWindow", "Monitor"))
        self.configButton.setText(_translate("MainWindow", "Configuration"))
        self.locationButton.setText(_translate("MainWindow", "Time Zone"))
        self.localTimeGroupBox.setTitle(
            _translate("MainWindow", "Local Time(Time Zone:8)"))
        self.localTimeLabel.setText(
            _translate("MainWindow", "2023-04-19 00:00:00"))
        self.utcTimeGroupBox.setTitle(_translate("MainWindow", "UTC Time"))
        self.utcTimeLabel.setText(
            _translate("MainWindow", "2023-04-19 00:00:00"))
