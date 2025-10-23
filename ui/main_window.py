"""主界面与装配逻辑。"""
from __future__ import annotations

from typing import Optional

from PyQt5 import QtCore, QtWidgets

from .components.navigation import NavigationBar
from .views.configuration import ConfigWizard, ConfigurationWorkspace
from .views.dashboard import MonitorDashboard


class MainWindowUI(QtCore.QObject):
    """负责搭建主界面布局，并暴露关键控件。"""

    monitor_view_index = 0
    config_view_index = 1
    report_view_index = 2

    navigationRequested = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._monitoring_active = False
        self._timezone_offset = 0

        self.central_widget: Optional[QtWidgets.QWidget] = None
        self.navigationBar: NavigationBar
        self.commandBar: QtWidgets.QFrame
        self.runStatusIndicator: QtWidgets.QLabel
        self.toggleMonitoringButton: QtWidgets.QPushButton
        self.reloadConfigButton: QtWidgets.QPushButton
        self.contentStack: QtWidgets.QStackedWidget
        self.configWizard: ConfigWizard
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

    def setup_ui(self, window: QtWidgets.QMainWindow) -> None:
        window.resize(1180, 760)
        window.setMinimumSize(960, 640)

        self.central_widget = QtWidgets.QWidget(window)
        self.central_widget.setObjectName("centralWidget")
        window.setCentralWidget(self.central_widget)

        root_layout = QtWidgets.QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.commandBar = QtWidgets.QFrame()
        self.commandBar.setObjectName("commandBar")
        command_layout = QtWidgets.QHBoxLayout(self.commandBar)
        command_layout.setContentsMargins(24, 12, 24, 12)
        command_layout.setSpacing(12)

        self.runStatusIndicator = QtWidgets.QLabel()
        self.runStatusIndicator.setObjectName("runStatusIndicator")
        self.runStatusIndicator.setProperty("role", "hint")
        command_layout.addWidget(self.runStatusIndicator)

        command_layout.addStretch(1)

        self.toggleMonitoringButton = QtWidgets.QPushButton()
        self.toggleMonitoringButton.setObjectName("toggleMonitoringButton")
        command_layout.addWidget(self.toggleMonitoringButton)

        self.reloadConfigButton = QtWidgets.QPushButton()
        self.reloadConfigButton.setObjectName("reloadConfigButton")
        command_layout.addWidget(self.reloadConfigButton)

        root_layout.addWidget(self.commandBar, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setObjectName("mainSplitter")
        root_layout.addWidget(splitter, 1)

        self.navigationBar = NavigationBar()
        splitter.addWidget(self.navigationBar)

        content_container = QtWidgets.QFrame()
        content_container.setObjectName("contentContainer")
        content_layout = QtWidgets.QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(16)
        splitter.addWidget(content_container)

        self.contentStack = QtWidgets.QStackedWidget()
        self.contentStack.setObjectName("contentStack")
        content_layout.addWidget(self.contentStack, 1)

        info_panel = QtWidgets.QFrame()
        info_panel.setObjectName("infoPanel")
        info_layout = QtWidgets.QVBoxLayout(info_panel)
        info_layout.setContentsMargins(16, 24, 16, 24)
        info_layout.setSpacing(12)

        self.timezoneHeading = QtWidgets.QLabel()
        self.timezoneHeading.setObjectName("timezoneHeading")
        self.timezoneHeading.setProperty("role", "heading")
        info_layout.addWidget(self.timezoneHeading)

        self.timezoneDisplay = QtWidgets.QLabel()
        self.timezoneDisplay.setObjectName("timezoneDisplay")
        info_layout.addWidget(self.timezoneDisplay)

        self.locationButton = QtWidgets.QPushButton()
        self.locationButton.setObjectName("locationButton")
        info_layout.addWidget(self.locationButton)

        info_layout.addSpacing(12)

        self.themeLabel = QtWidgets.QLabel()
        self.themeLabel.setObjectName("themeLabel")
        self.themeLabel.setProperty("role", "hint")
        info_layout.addWidget(self.themeLabel)

        self.themeSelector = QtWidgets.QComboBox()
        self.themeSelector.setObjectName("themeSelector")
        self.themeSelector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        info_layout.addWidget(self.themeSelector)

        self.languageLabel = QtWidgets.QLabel()
        self.languageLabel.setObjectName("languageLabel")
        self.languageLabel.setProperty("role", "hint")
        info_layout.addWidget(self.languageLabel)

        self.languageSelector = QtWidgets.QComboBox()
        self.languageSelector.setObjectName("languageSelector")
        self.languageSelector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        info_layout.addWidget(self.languageSelector)

        info_layout.addStretch(1)

        splitter.addWidget(info_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        monitor_page = MonitorDashboard()
        self.contentStack.addWidget(monitor_page)

        self.configWizard = ConfigWizard()
        configuration_page = ConfigurationWorkspace(self.configWizard)
        configuration_page.setObjectName("configurationWorkspace")
        self.contentStack.addWidget(configuration_page)

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

    def show_reports_page(self) -> None:
        self.contentStack.setCurrentIndex(self.report_view_index)
        self.navigationBar.set_active("reports")

    def update_monitoring_controls(self, running: bool) -> None:
        self._monitoring_active = running
        self.toggleMonitoringButton.setText(
            self.tr("关闭 Close") if running else self.tr("启动 Start")
        )
        self.runStatusIndicator.setText(
            self.tr("运行中 Running") if running else self.tr("待命 Standby")
        )

    def set_timezone_hint(self, timezone: int) -> None:
        self._timezone_offset = timezone
        self.timezoneDisplay.setText(
            self.tr("当前时区: UTC{offset:+d}").format(offset=timezone)
        )

    def retranslate_ui(self) -> None:
        self.commandBar.setToolTip(self.tr("全局操作"))
        self.runStatusIndicator.setText(
            self.tr("运行中 Running")
            if self._monitoring_active
            else self.tr("待命 Standby")
        )
        self.toggleMonitoringButton.setText(
            self.tr("关闭 Close")
            if self._monitoring_active
            else self.tr("启动 Start")
        )
        self.reloadConfigButton.setText(self.tr("重载配置 Reload"))

        self.navigationBar.retranslate_ui()

        self.timezoneHeading.setText(self.tr("运行信息 Runtime"))
        self.timezoneDisplay.setText(
            self.tr("当前时区: UTC{offset:+d}").format(offset=self._timezone_offset)
        )
        self.locationButton.setText(self.tr("设置时区 Set Timezone"))

        self.themeLabel.setText(self.tr("主题 Theme"))
        self.themeSelector.setToolTip(self.tr("选择主题"))
        self.languageLabel.setText(self.tr("语言 Language"))
        self.languageSelector.setToolTip(self.tr("选择语言"))

        monitor_page = self.contentStack.widget(self.monitor_view_index)
        if isinstance(monitor_page, MonitorDashboard):
            monitor_page.retranslate_ui()
        configuration_page = self.contentStack.widget(self.config_view_index)
        if isinstance(configuration_page, ConfigurationWorkspace):
            configuration_page.retranslate_ui()

        self.reportPlaceholderLabel.setText(
            self.tr("Reports and alerts view under construction. Stay tuned!")
        )


__all__ = [
    "MainWindowUI",
    "NavigationBar",
    "MonitorDashboard",
    "ConfigWizard",
    "ConfigurationWorkspace",
]
