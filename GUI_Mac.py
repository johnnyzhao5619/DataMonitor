# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 12:32 a.m.
# @Author: weijiazhao
# @File : GUI_Mac.py

from PyQt5 import QtCore, QtGui, QtWidgets
import configuration


# time_zone = configuration.get_timezone()
# main window
class MainWindow(object):

    def setupUi(self, monitor: QtWidgets.QMainWindow) -> None:
        """
        Setup the main window UI

        Parameters
        ----------
        monitor : QtWidgets.QMainWindow
            The main window to be setup
        """
        global switch

        monitor.setMinimumSize(QtCore.QSize(720, 500))
        monitor.setMaximumSize(QtCore.QSize(720, 1000))

        self.monitor_layout = QtWidgets.QWidget(monitor)
        self.monitor_layout.setGeometry(QtCore.QRect(0, 0, 720, 500))
        self.main_layout = QtWidgets.QVBoxLayout(self.monitor_layout)

        # Button
        self.button_layout = QtWidgets.QHBoxLayout(monitor)

        self.switch_button = QtWidgets.QPushButton('Monitor')
        self.switch_button.setMaximumSize(QtCore.QSize(120, 35))
        self.switch_button.setMinimumSize(QtCore.QSize(120, 35))

        self.config_button = QtWidgets.QPushButton('Configuration')
        self.config_button.setMaximumSize(QtCore.QSize(150, 35))
        self.config_button.setMinimumSize(QtCore.QSize(150, 35))

        self.location_button = QtWidgets.QPushButton('Time Zone')
        self.location_button.setMaximumSize(QtCore.QSize(150, 35))
        self.location_button.setMinimumSize(QtCore.QSize(150, 35))

        # add buttons to buttonlayout
        self.button_layout.addWidget(self.switch_button)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.config_button)
        self.button_layout.addWidget(self.location_button)

        # Create localTimeGroupBox
        self.local_time_group_box = QtWidgets.QGroupBox(
            f'Local Time(Time Zone: {configuration.get_timezone()})')
        # self.localTimeGroupBox.setGeometry(QtCore.QRect(10, 70, 340, 80))

        self.local_time_layout = QtWidgets.QVBoxLayout()
        self.local_time_group_box.setLayout(self.local_time_layout)
        self.local_time_group_box.setMinimumSize(QtCore.QSize(340, 80))
        self.local_time_group_box.setMaximumSize(QtCore.QSize(340, 80))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.local_time_group_box.setFont(font)
        # Create LocalTimeLabel
        self.local_time_label = QtWidgets.QLabel(self.local_time_group_box)
        self.local_time_label.setMaximumSize(QtCore.QSize(320, 50))
        self.local_time_label.setMaximumSize(QtCore.QSize(320, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(26)
        font.setBold(True)
        font.setWeight(75)
        self.local_time_label.setFont(font)
        self.local_time_layout.addWidget(self.local_time_label)

        # Create UTCTimeGroupBox
        self.utc_time_group_box = QtWidgets.QGroupBox('UTC Time')
        self.utc_time_group_box.setGeometry(QtCore.QRect(350, 70, 340, 80))

        self.utc_time_layout = QtWidgets.QVBoxLayout()
        self.utc_time_group_box.setLayout(self.utc_time_layout)
        self.utc_time_group_box.setMinimumSize(QtCore.QSize(340, 80))
        self.utc_time_group_box.setMaximumSize(QtCore.QSize(340, 80))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.utc_time_group_box.setFont(font)

        # utcTimeLabel
        self.utc_time_label = QtWidgets.QLabel(self.utc_time_group_box)
        self.utc_time_label.setMaximumSize(QtCore.QSize(320, 50))
        self.utc_time_label.setMaximumSize(QtCore.QSize(320, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(26)
        font.setBold(True)
        font.setWeight(75)
        self.utc_time_label.setFont(font)
        self.utc_time_layout.addWidget(self.utc_time_label)

        # create the timer to update the clock
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(100)

        self.log_line = QtWidgets.QFrame()
        self.log_line.setFrameShape(QtWidgets.QFrame.HLine)
        self.log_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.monitor_browser = QtWidgets.QTextBrowser()
        self.monitor_browser.setGeometry(QtCore.QRect(10, 10, 700, 300))

        self.monitor_browser.setMinimumSize(QtCore.QSize(700, 300))
        self.monitor_browser.setMaximumSize(QtCore.QSize(700, 300))

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.monitor_browser.setFont(font)
        self.main_layout.addLayout(self.button_layout)

        # add clock to the layout
        self.time_layout = QtWidgets.QHBoxLayout()
        self.time_layout.addWidget(self.local_time_group_box)
        self.time_layout.addWidget(self.utc_time_group_box)
        self.main_layout.addLayout(self.time_layout)

        # add monitor to the layout
        self.main_layout.addWidget(self.log_line)
        self.main_layout.addWidget(self.monitor_browser)

        self.main_layout.addStretch(1)
