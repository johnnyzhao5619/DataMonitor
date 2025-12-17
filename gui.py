# -*- coding: utf-8 -*-
# Unified GUI for cross-platform adaptive layout

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer


class MainWindow(object):

    def setupUi(self, main_window: QtWidgets.QMainWindow) -> None:
        main_window.setObjectName("MainWindow")
        main_window.resize(900, 600)
        main_window.setMinimumSize(QtCore.QSize(720, 500))
        main_window.setMaximumSize(QtCore.QSize(1600, 1200))

        self.centralwidget = QtWidgets.QWidget(main_window)
        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Top buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(10)

        self.switchButton = QtWidgets.QPushButton(self.centralwidget)
        self.switchButton.setMinimumSize(QtCore.QSize(120, 35))
        self.switchButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                        QtWidgets.QSizePolicy.Fixed)
        font_bold = QtGui.QFont()
        font_bold.setPointSize(9)
        font_bold.setBold(True)
        self.switchButton.setFont(font_bold)

        self.settingsButton = QtWidgets.QPushButton(self.centralwidget)
        self.settingsButton.setMinimumSize(QtCore.QSize(130, 35))
        self.settingsButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                          QtWidgets.QSizePolicy.Fixed)
        self.settingsButton.setFont(font_bold)

        self.reloadConfigButton = QtWidgets.QPushButton(self.centralwidget)
        self.reloadConfigButton.setMinimumSize(QtCore.QSize(130, 35))
        self.reloadConfigButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                              QtWidgets.QSizePolicy.Fixed)
        self.reloadConfigButton.setFont(font_bold)

        button_layout.addWidget(self.switchButton, 0)
        button_layout.addStretch(1)
        button_layout.addWidget(self.settingsButton, 0)
        button_layout.addWidget(self.reloadConfigButton, 0)
        main_layout.addLayout(button_layout)

        # Time display
        time_layout = QtWidgets.QHBoxLayout()
        time_layout.setSpacing(12)

        time_group_font = QtGui.QFont()
        time_group_font.setPointSize(10)
        time_group_font.setBold(True)

        self.localTimeGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.localTimeGroupBox.setFont(time_group_font)
        local_layout = QtWidgets.QVBoxLayout(self.localTimeGroupBox)
        local_layout.setContentsMargins(10, 10, 10, 10)
        self.localTimeLabel = QtWidgets.QLabel(self.localTimeGroupBox)
        local_time_font = QtGui.QFont()
        local_time_font.setPointSize(12)
        local_time_font.setBold(True)
        self.localTimeLabel.setFont(local_time_font)
        self.localTimeLabel.setMinimumHeight(28)
        local_layout.addWidget(self.localTimeLabel)

        self.utcTimeGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.utcTimeGroupBox.setFont(time_group_font)
        utc_layout = QtWidgets.QVBoxLayout(self.utcTimeGroupBox)
        utc_layout.setContentsMargins(10, 10, 10, 10)
        self.utcTimeLabel = QtWidgets.QLabel(self.utcTimeGroupBox)
        self.utcTimeLabel.setFont(local_time_font)
        self.utcTimeLabel.setMinimumHeight(28)
        utc_layout.addWidget(self.utcTimeLabel)

        time_layout.addWidget(self.localTimeGroupBox, 1)
        time_layout.addWidget(self.utcTimeGroupBox, 1)
        main_layout.addLayout(time_layout)

        # Separator
        line = QtWidgets.QFrame(self.centralwidget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        # Controls for log behavior
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.setSpacing(10)
        self.autoScrollCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.autoScrollCheckBox.setChecked(True)
        self.autoScrollCheckBox.setText("Auto Scroll")
        self.clearLogButton = QtWidgets.QPushButton("Clear Log",
                                                    self.centralwidget)
        self.clearLogButton.setMinimumSize(QtCore.QSize(90, 28))
        self.clearLogButton.setFont(QtGui.QFont("", 9))
        self.copyLogButton = QtWidgets.QPushButton("Copy Log",
                                                   self.centralwidget)
        self.copyLogButton.setMinimumSize(QtCore.QSize(90, 28))
        self.copyLogButton.setFont(QtGui.QFont("", 9))
        control_layout.addWidget(self.autoScrollCheckBox)
        control_layout.addStretch(1)
        control_layout.addWidget(self.clearLogButton)
        control_layout.addWidget(self.copyLogButton)
        main_layout.addLayout(control_layout)

        # Monitor log output
        self.monitorBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.monitorBrowser.setFont(QtGui.QFont("", 9))
        self.monitorBrowser.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                          QtWidgets.QSizePolicy.Expanding)
        self.monitorBrowser.setMinimumHeight(280)
        main_layout.addWidget(self.monitorBrowser, 1)

        main_window.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(main_window)
        main_window.setStatusBar(self.statusbar)

        self.retranslateUi(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

        # Timer to update the clock, 1s interval to reduce CPU usage
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def retranslateUi(self, main_window: QtWidgets.QMainWindow) -> None:
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.switchButton.setText(_translate("MainWindow", "Monitor"))
        self.switchButton.setShortcut(_translate("MainWindow", "Alt+M"))
        self.settingsButton.setText(_translate("MainWindow", "Settings"))
        self.settingsButton.setShortcut(_translate("MainWindow", "Alt+S"))
        self.reloadConfigButton.setText(
            _translate("MainWindow", "Reload Config"))
        self.reloadConfigButton.setShortcut(
            _translate("MainWindow", "Alt+R"))
        self.autoScrollCheckBox.setText(
            _translate("MainWindow", "Auto Scroll"))
        self.localTimeGroupBox.setTitle(
            _translate("MainWindow", "Local Time (UTC Offset)"))
        self.localTimeLabel.setText(
            _translate("MainWindow", "2023-04-19 00:00:00"))
        self.utcTimeGroupBox.setTitle(_translate("MainWindow", "UTC Time"))
        self.utcTimeLabel.setText(
            _translate("MainWindow", "2023-04-19 00:00:00"))

        # Tab order for keyboard navigation
        QtWidgets.QWidget.setTabOrder(self.switchButton,
                                      self.settingsButton)
        QtWidgets.QWidget.setTabOrder(self.settingsButton,
                                      self.reloadConfigButton)
        QtWidgets.QWidget.setTabOrder(self.reloadConfigButton,
                                      self.autoScrollCheckBox)
        QtWidgets.QWidget.setTabOrder(self.autoScrollCheckBox,
                                      self.clearLogButton)
        QtWidgets.QWidget.setTabOrder(self.clearLogButton,
                                      self.copyLogButton)
        QtWidgets.QWidget.setTabOrder(self.copyLogButton,
                                      self.monitorBrowser)
