"""主界面与装配逻辑。"""
from __future__ import annotations

from typing import Dict, Optional

from PySide6 import QtCore, QtWidgets

from .components.navigation import NavigationBar
from .views.configuration import ConfigWizard, ConfigurationWorkspace
from .views.dashboard import MonitorDashboard
from .views.preferences import PreferencesPage
from .views.documentation import DocumentationPage


class MainWindowUI(QtCore.QObject):
    """负责搭建主界面布局，并暴露关键控件。"""
    navigationRequested = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._monitoring_active = False
        self._timezone_offset = 0
        self._views: Dict[str, QtWidgets.QWidget] = {}
        self._view_indexes: Dict[str, int] = {}

        self.central_widget: Optional[QtWidgets.QWidget] = None
        self.navigationBar: NavigationBar
        self.commandBar: QtWidgets.QFrame
        self.toggleMonitoringButton: QtWidgets.QPushButton
        self.reloadConfigButton: QtWidgets.QPushButton
        self.exitButton: QtWidgets.QPushButton
        self.contentStack: QtWidgets.QStackedWidget
        self.configWizard: ConfigWizard
        self.preferencesPage: PreferencesPage
        self.documentationPage: DocumentationPage
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
        self.loggingGroup: QtWidgets.QWidget
        self.logLevelCombo: QtWidgets.QComboBox
        self.logDirectoryEdit: QtWidgets.QLineEdit
        self.logDirectoryBrowse: QtWidgets.QPushButton
        self.logFileEdit: QtWidgets.QLineEdit
        self.logMaxSizeSpin: QtWidgets.QDoubleSpinBox
        self.logMaxSizeSuffix: QtWidgets.QLabel
        self.logBackupSpin: QtWidgets.QSpinBox
        self.logConsoleCheck: QtWidgets.QCheckBox
        self.logFormatEdit: QtWidgets.QLineEdit
        self.logDatefmtEdit: QtWidgets.QLineEdit
        self.saveLoggingButton: QtWidgets.QPushButton
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
        self._register_view("monitor", monitor_page)

        self.configWizard = ConfigWizard()
        configuration_page = ConfigurationWorkspace(self.configWizard)
        configuration_page.setObjectName("configurationWorkspace")
        self._register_view("configuration", configuration_page)

        self.preferencesPage = PreferencesPage()
        self._register_view("preferences", self.preferencesPage)

        self.documentationPage = DocumentationPage()
        self._register_view("documentation", self.documentationPage)

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
        self._register_view("reports", reports_placeholder)

        self.monitor_view_index = self._view_indexes["monitor"]
        self.config_view_index = self._view_indexes["configuration"]
        self.preferences_view_index = self._view_indexes["preferences"]
        self.documentation_view_index = self._view_indexes["documentation"]
        self.report_view_index = self._view_indexes["reports"]

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
        self.loggingGroup = self.preferencesPage.loggingGroup
        self.logLevelCombo = self.preferencesPage.logLevelCombo
        self.logDirectoryEdit = self.preferencesPage.logDirectoryEdit
        self.logDirectoryBrowse = self.preferencesPage.logDirectoryBrowse
        self.logFileEdit = self.preferencesPage.logFileEdit
        self.logMaxSizeSpin = self.preferencesPage.logMaxSizeSpin
        self.logMaxSizeSuffix = self.preferencesPage.logMaxSizeSuffix
        self.logBackupSpin = self.preferencesPage.logBackupSpin
        self.logConsoleCheck = self.preferencesPage.logConsoleCheck
        self.logFormatEdit = self.preferencesPage.logFormatEdit
        self.logDatefmtEdit = self.preferencesPage.logDatefmtEdit
        self.saveLoggingButton = self.preferencesPage.saveLoggingButton

        self.navigationBar.navigationTriggered.connect(self.navigationRequested.emit)

        self.retranslate_ui()
        self.show_monitor_page()

    # 导航方法
    def show_monitor_page(self) -> None:
        self._show_view("monitor")

    def show_configuration_page(self) -> None:
        self._show_view("configuration")

    def show_preferences_page(self) -> None:
        self._show_view("preferences")

    def show_documentation_page(self) -> None:
        self._show_view("documentation")

    def show_reports_page(self) -> None:
        self._show_view("reports")

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
        self.timezoneDisplay.setText(
            self.tr("Current Timezone: UTC{offset:+d}").format(offset=self._timezone_offset)
        )

        for widget in self._views.values():
            retranslate = getattr(widget, "retranslate_ui", None)
            if callable(retranslate):
                retranslate()

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

    # ------------------------------------------------------------------
    def _register_view(self, nav_id: str, widget: QtWidgets.QWidget) -> None:
        index = self.contentStack.addWidget(widget)
        self._views[nav_id] = widget
        self._view_indexes[nav_id] = index

    def _show_view(self, nav_id: str) -> None:
        index = self._view_indexes.get(nav_id)
        if index is None:
            return
        self.contentStack.setCurrentIndex(index)
        self.navigationBar.set_active(nav_id)


__all__ = [
    "MainWindowUI",
    "NavigationBar",
    "MonitorDashboard",
    "ConfigWizard",
    "ConfigurationWorkspace",
    "PreferencesPage",
    "DocumentationPage",
]
