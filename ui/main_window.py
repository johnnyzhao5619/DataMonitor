"""主界面与装配逻辑。"""
from __future__ import annotations

from typing import Optional

from PyQt5 import QtCore, QtWidgets

from .components.navigation import NavigationBar
from .views.configuration import ConfigWizard, ConfigurationWorkspace
from .views.dashboard import MonitorDashboard
from .views.preferences import PreferencesPage


class MainWindowUI(QtCore.QObject):
    """负责搭建主界面布局，并暴露关键控件。"""

    monitor_view_index = 0
    config_view_index = 1
    preferences_view_index = 2
    report_view_index = 3

    navigationRequested = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._monitoring_active = False
        self._timezone_offset = 0

        self.central_widget: Optional[QtWidgets.QWidget] = None
        self.navigationBar: NavigationBar
        self.commandBar: QtWidgets.QFrame
        self.toggleMonitoringButton: QtWidgets.QPushButton
        self.reloadConfigButton: QtWidgets.QPushButton
        self.exitButton: QtWidgets.QPushButton
        self.contentStack: QtWidgets.QStackedWidget
        self.configWizard: ConfigWizard
        self.preferencesPage: PreferencesPage
        self.localTimeGroupBox: QtWidgets.QGroupBox
        self.localTimeLabel: QtWidgets.QLabel
        self.utcTimeGroupBox: QtWidgets.QGroupBox
        self.utcTimeLabel: QtWidgets.QLabel
        self.monitorBrowser: QtWidgets.QTextBrowser
        self.locationButton: QtWidgets.QPushButton
        self.themeLabel: QtWidgets.QLabel
        self.themeSelector: QtWidgets.QComboBox
        self.languageLabel: QtWidgets.QLabel
        self.languageSelector: QtWidgets.QComboBox
        self.timezoneHeading: QtWidgets.QLabel
        self.timezoneDisplay: QtWidgets.QLabel
        self.reportPlaceholderLabel: QtWidgets.QLabel
        self._status_text: str = ""

    def setup_ui(self, window: QtWidgets.QMainWindow) -> None:
        window.resize(1180, 760)
        window.setMinimumSize(960, 640)

        self.central_widget = QtWidgets.QWidget(window)
        self.central_widget.setObjectName("centralWidget")
        window.setCentralWidget(self.central_widget)

        root_layout = QtWidgets.QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        root_layout.addWidget(splitter, 1)

        self.navigationBar = NavigationBar()
        splitter.addWidget(self.navigationBar)

        content_container = QtWidgets.QFrame()
        content_container.setObjectName("contentContainer")
        content_layout = QtWidgets.QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 16, 24, 24)
        content_layout.setSpacing(16)
        splitter.addWidget(content_container)

        self.commandBar = QtWidgets.QFrame()
        self.commandBar.setObjectName("commandBar")
        command_layout = QtWidgets.QHBoxLayout(self.commandBar)
        command_layout.setContentsMargins(0, 0, 0, 0)
        command_layout.setSpacing(12)

        command_layout.addStretch(1)

        self.toggleMonitoringButton = QtWidgets.QPushButton()
        self.toggleMonitoringButton.setObjectName("toggleMonitoringButton")
        command_layout.addWidget(self.toggleMonitoringButton)

        self.reloadConfigButton = QtWidgets.QPushButton()
        self.reloadConfigButton.setObjectName("reloadConfigButton")
        command_layout.addWidget(self.reloadConfigButton)

        self.exitButton = QtWidgets.QPushButton()
        self.exitButton.setObjectName("exitButton")
        command_layout.addWidget(self.exitButton)

        content_layout.addWidget(self.commandBar, 0)

        self.contentStack = QtWidgets.QStackedWidget()
        self.contentStack.setObjectName("contentStack")
        content_layout.addWidget(self.contentStack, 1)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        monitor_page = MonitorDashboard()
        self.contentStack.addWidget(monitor_page)

        self.configWizard = ConfigWizard()
        configuration_page = ConfigurationWorkspace(self.configWizard)
        configuration_page.setObjectName("configurationWorkspace")
        self.contentStack.addWidget(configuration_page)

        self.preferencesPage = PreferencesPage()
        self.contentStack.addWidget(self.preferencesPage)

        reports_placeholder = QtWidgets.QFrame()
        reports_placeholder.setObjectName("reportsPlaceholder")
        placeholder_layout = QtWidgets.QVBoxLayout(reports_placeholder)
        placeholder_layout.setContentsMargins(16, 16, 16, 16)
        placeholder_layout.addStretch(1)
        self.reportPlaceholderLabel = QtWidgets.QLabel()
        self.reportPlaceholderLabel.setObjectName("reportsPlaceholderLabel")
        self.reportPlaceholderLabel.setAlignment(QtCore.Qt.AlignCenter)
        placeholder_layout.addWidget(self.reportPlaceholderLabel)
        placeholder_layout.addStretch(1)
        self.contentStack.addWidget(reports_placeholder)

        self.localTimeGroupBox = monitor_page.localTimeGroupBox
        self.localTimeLabel = monitor_page.localTimeLabel
        self.utcTimeGroupBox = monitor_page.utcTimeGroupBox
        self.utcTimeLabel = monitor_page.utcTimeLabel
        self.monitorBrowser = monitor_page.monitorBrowser
        self.timezoneHeading = self.preferencesPage.timezoneHeading
        self.timezoneDisplay = self.preferencesPage.timezoneDisplay
        self.locationButton = self.preferencesPage.locationButton
        self.themeLabel = self.preferencesPage.themeLabel
        self.themeSelector = self.preferencesPage.themeSelector
        self.languageLabel = self.preferencesPage.languageLabel
        self.languageSelector = self.preferencesPage.languageSelector

        self.navigationBar.navigationTriggered.connect(self.navigationRequested.emit)

        self.retranslate_ui()
        self.show_monitor_page()

    # 导航方法
    def show_monitor_page(self) -> None:
        self.contentStack.setCurrentIndex(self.monitor_view_index)
        self.navigationBar.set_active("monitor")

    def show_configuration_page(self) -> None:
        self.contentStack.setCurrentIndex(self.config_view_index)
        self.navigationBar.set_active("configuration")

    def show_preferences_page(self) -> None:
        self.contentStack.setCurrentIndex(self.preferences_view_index)
        self.navigationBar.set_active("preferences")

    def show_reports_page(self) -> None:
        self.contentStack.setCurrentIndex(self.report_view_index)
        self.navigationBar.set_active("reports")

    def update_monitoring_controls(self, running: bool) -> None:
        self._monitoring_active = running
        self.toggleMonitoringButton.setText(
            self.tr("Stop") if running else self.tr("Start")
        )
        self._status_text = (
            self.tr("Running")
            if self._monitoring_active
            else self.tr("Standby")
        )

    def set_timezone_hint(self, timezone: int) -> None:
        self._timezone_offset = timezone
        self.timezoneDisplay.setText(
            self.tr("Current Timezone: UTC{offset:+d}").format(offset=timezone)
        )

    def retranslate_ui(self) -> None:
        self.commandBar.setToolTip(self.tr("Global Actions"))
        self.toggleMonitoringButton.setText(
            self.tr("Stop")
            if self._monitoring_active
            else self.tr("Start")
        )
        self._status_text = (
            self.tr("Running")
            if self._monitoring_active
            else self.tr("Standby")
        )
        self.reloadConfigButton.setText(self.tr("Reload"))
        self.exitButton.setText(self.tr("Exit"))

        self.navigationBar.retranslate_ui()

        self.preferencesPage.retranslate_ui()
        self.timezoneDisplay.setText(
            self.tr("Current Timezone: UTC{offset:+d}").format(offset=self._timezone_offset)
        )

        monitor_page = self.contentStack.widget(self.monitor_view_index)
        if isinstance(monitor_page, MonitorDashboard):
            monitor_page.retranslate_ui()
        configuration_page = self.contentStack.widget(self.config_view_index)
        if isinstance(configuration_page, ConfigurationWorkspace):
            configuration_page.retranslate_ui()

        self.reportPlaceholderLabel.setText(
            self.tr("Reports and alerts view under construction. Stay tuned!")
        )

    def current_status_text(self) -> str:
        if not self._status_text:
            self._status_text = (
                self.tr("Running")
                if self._monitoring_active
                else self.tr("Standby")
            )
        return self._status_text


__all__ = [
    "MainWindowUI",
    "NavigationBar",
    "MonitorDashboard",
    "ConfigWizard",
    "ConfigurationWorkspace",
    "PreferencesPage",
]
