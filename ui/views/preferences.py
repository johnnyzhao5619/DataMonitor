"""Preferences page view containing runtime and display settings."""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class PreferencesPage(QtWidgets.QWidget):
    """Settings page housing timezone, theme, and language controls."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("preferencesPage")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.timezoneHeading = QtWidgets.QLabel(self)
        self.timezoneHeading.setObjectName("timezoneHeading")
        self.timezoneHeading.setProperty("role", "heading")
        layout.addWidget(self.timezoneHeading)

        self.timezoneDisplay = QtWidgets.QLabel(self)
        self.timezoneDisplay.setObjectName("timezoneDisplay")
        layout.addWidget(self.timezoneDisplay)

        self.locationButton = QtWidgets.QPushButton(self)
        self.locationButton.setObjectName("locationButton")
        layout.addWidget(self.locationButton)

        layout.addSpacing(12)

        self.themeLabel = QtWidgets.QLabel(self)
        self.themeLabel.setObjectName("themeLabel")
        self.themeLabel.setProperty("role", "hint")
        layout.addWidget(self.themeLabel)

        self.themeSelector = QtWidgets.QComboBox(self)
        self.themeSelector.setObjectName("themeSelector")
        self.themeSelector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(self.themeSelector)

        self.languageLabel = QtWidgets.QLabel(self)
        self.languageLabel.setObjectName("languageLabel")
        self.languageLabel.setProperty("role", "hint")
        layout.addWidget(self.languageLabel)

        self.languageSelector = QtWidgets.QComboBox(self)
        self.languageSelector.setObjectName("languageSelector")
        self.languageSelector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(self.languageSelector)

        layout.addSpacing(12)

        self.loggingCard = QtWidgets.QWidget(self)
        self.loggingCard.setObjectName("loggingCard")
        self.loggingCard.setProperty("role", "card")
        self.loggingCard.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.loggingCard.setMinimumHeight(360)
        self.loggingGroup = self.loggingCard  # backward compatibility

        logging_container = QtWidgets.QVBoxLayout(self.loggingCard)
        logging_container.setContentsMargins(16, 16, 16, 16)
        logging_container.setSpacing(12)

        self.logHeaderLabel = QtWidgets.QLabel(self.loggingCard)
        self.logHeaderLabel.setObjectName("logHeaderLabel")
        self.logHeaderLabel.setProperty("role", "heading")
        logging_container.addWidget(self.logHeaderLabel)

        self.logDescriptionLabel = QtWidgets.QLabel(self.loggingCard)
        self.logDescriptionLabel.setObjectName("logDescriptionLabel")
        self.logDescriptionLabel.setWordWrap(True)
        self.logDescriptionLabel.setProperty("role", "hint")
        logging_container.addWidget(self.logDescriptionLabel)

        form_layout = QtWidgets.QGridLayout()
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(16)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setColumnStretch(1, 1)
        logging_container.addLayout(form_layout)

        component_height = 38

        self.logLevelLabel = QtWidgets.QLabel(self.loggingCard)
        self.logLevelLabel.setObjectName("logLevelLabel")
        self.logLevelLabel.setProperty("role", "hint")
        self.logLevelCombo = QtWidgets.QComboBox(self.loggingCard)
        self.logLevelCombo.setObjectName("logLevelCombo")
        self.logLevelCombo.setFixedWidth(160)
        self.logLevelCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.logLevelCombo.setMinimumHeight(component_height)
        form_layout.addWidget(self.logLevelLabel, 0, 0)
        form_layout.addWidget(self.logLevelCombo, 0, 1)

        self.logDirectoryLabel = QtWidgets.QLabel(self.loggingCard)
        self.logDirectoryLabel.setObjectName("logDirectoryLabel")
        self.logDirectoryLabel.setProperty("role", "hint")
        directory_box = QtWidgets.QWidget(self.loggingCard)
        directory_layout = QtWidgets.QHBoxLayout(directory_box)
        directory_layout.setContentsMargins(0, 0, 0, 0)
        directory_layout.setSpacing(8)
        self.logDirectoryEdit = QtWidgets.QLineEdit(directory_box)
        self.logDirectoryEdit.setObjectName("logDirectoryEdit")
        self.logDirectoryEdit.setClearButtonEnabled(True)
        self.logDirectoryEdit.setMinimumHeight(component_height)
        self.logDirectoryBrowse = QtWidgets.QPushButton(directory_box)
        self.logDirectoryBrowse.setObjectName("logDirectoryBrowse")
        self.logDirectoryBrowse.setMinimumHeight(component_height)
        directory_layout.addWidget(self.logDirectoryEdit, 1)
        directory_layout.addWidget(self.logDirectoryBrowse, 0)
        form_layout.addWidget(self.logDirectoryLabel, 1, 0)
        form_layout.addWidget(directory_box, 1, 1)

        self.logFileLabel = QtWidgets.QLabel(self.loggingCard)
        self.logFileLabel.setObjectName("logFileLabel")
        self.logFileLabel.setProperty("role", "hint")
        self.logFileEdit = QtWidgets.QLineEdit(self.loggingCard)
        self.logFileEdit.setObjectName("logFileEdit")
        self.logFileEdit.setClearButtonEnabled(True)
        self.logFileEdit.setMinimumHeight(component_height)
        form_layout.addWidget(self.logFileLabel, 2, 0)
        form_layout.addWidget(self.logFileEdit, 2, 1)

        self.logMaxSizeLabel = QtWidgets.QLabel(self.loggingCard)
        self.logMaxSizeLabel.setObjectName("logMaxSizeLabel")
        self.logMaxSizeLabel.setProperty("role", "hint")
        max_size_box = QtWidgets.QWidget(self.loggingCard)
        max_size_layout = QtWidgets.QHBoxLayout(max_size_box)
        max_size_layout.setContentsMargins(0, 0, 0, 0)
        max_size_layout.setSpacing(8)
        self.logMaxSizeSpin = QtWidgets.QDoubleSpinBox(max_size_box)
        self.logMaxSizeSpin.setObjectName("logMaxSizeSpin")
        self.logMaxSizeSpin.setDecimals(1)
        self.logMaxSizeSpin.setRange(0.0, 4096.0)
        self.logMaxSizeSpin.setSingleStep(1.0)
        self.logMaxSizeSpin.setMinimumHeight(component_height)
        self.logMaxSizeSuffix = QtWidgets.QLabel(max_size_box)
        self.logMaxSizeSuffix.setObjectName("logMaxSizeSuffix")
        max_size_layout.addWidget(self.logMaxSizeSpin)
        max_size_layout.addWidget(self.logMaxSizeSuffix)
        form_layout.addWidget(self.logMaxSizeLabel, 3, 0)
        form_layout.addWidget(max_size_box, 3, 1)

        self.logBackupLabel = QtWidgets.QLabel(self.loggingCard)
        self.logBackupLabel.setObjectName("logBackupLabel")
        self.logBackupLabel.setProperty("role", "hint")
        self.logBackupSpin = QtWidgets.QSpinBox(self.loggingCard)
        self.logBackupSpin.setObjectName("logBackupSpin")
        self.logBackupSpin.setRange(0, 100)
        self.logBackupSpin.setMinimumHeight(component_height)
        form_layout.addWidget(self.logBackupLabel, 4, 0)
        form_layout.addWidget(self.logBackupSpin, 4, 1)

        self.logConsoleLabel = QtWidgets.QLabel(self.loggingCard)
        self.logConsoleLabel.setObjectName("logConsoleLabel")
        self.logConsoleLabel.setProperty("role", "hint")
        self.logConsoleCheck = QtWidgets.QCheckBox(self.loggingCard)
        self.logConsoleCheck.setObjectName("logConsoleCheck")
        self.logConsoleCheck.setMinimumHeight(component_height)
        form_layout.addWidget(self.logConsoleLabel, 5, 0)
        form_layout.addWidget(self.logConsoleCheck, 5, 1)

        self.logFormatLabel = QtWidgets.QLabel(self.loggingCard)
        self.logFormatLabel.setObjectName("logFormatLabel")
        self.logFormatLabel.setProperty("role", "hint")
        self.logFormatEdit = QtWidgets.QLineEdit(self.loggingCard)
        self.logFormatEdit.setObjectName("logFormatEdit")
        self.logFormatEdit.setClearButtonEnabled(True)
        self.logFormatEdit.setMinimumHeight(component_height)
        form_layout.addWidget(self.logFormatLabel, 6, 0)
        form_layout.addWidget(self.logFormatEdit, 6, 1)

        self.logDatefmtLabel = QtWidgets.QLabel(self.loggingCard)
        self.logDatefmtLabel.setObjectName("logDatefmtLabel")
        self.logDatefmtLabel.setProperty("role", "hint")
        self.logDatefmtEdit = QtWidgets.QLineEdit(self.loggingCard)
        self.logDatefmtEdit.setObjectName("logDatefmtEdit")
        self.logDatefmtEdit.setClearButtonEnabled(True)
        self.logDatefmtEdit.setMinimumHeight(component_height)
        form_layout.addWidget(self.logDatefmtLabel, 7, 0)
        form_layout.addWidget(self.logDatefmtEdit, 7, 1)

        self.loggingHintLabel = QtWidgets.QLabel(self.loggingCard)
        self.loggingHintLabel.setObjectName("loggingHintLabel")
        self.loggingHintLabel.setWordWrap(True)
        self.loggingHintLabel.setProperty("role", "hint")
        logging_container.addWidget(self.loggingHintLabel)

        self.saveLoggingButton = QtWidgets.QPushButton(self.loggingCard)
        self.saveLoggingButton.setObjectName("saveLoggingButton")
        self.saveLoggingButton.setMinimumHeight(component_height)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch(1)
        button_layout.addWidget(self.saveLoggingButton, 0, QtCore.Qt.AlignRight)
        logging_container.addLayout(button_layout)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setObjectName("loggingScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidget(self.loggingCard)
        self.loggingScrollArea = scroll

        layout.addWidget(scroll)

        layout.addStretch(1)

    def retranslate_ui(self) -> None:
        self.timezoneHeading.setText(self.tr("Runtime Information"))
        self.locationButton.setText(self.tr("Set Timezone"))
        self.themeLabel.setText(self.tr("Theme"))
        self.themeSelector.setToolTip(self.tr("Select Theme"))
        self.languageLabel.setText(self.tr("Language"))
        self.languageSelector.setToolTip(self.tr("Select Language"))
        self.logHeaderLabel.setText(self.tr("Logging Settings"))
        self.logDescriptionLabel.setText(
            self.tr("Configure the log destination, rotation policy, and formatting for application output.")
        )
        self.logLevelLabel.setText(self.tr("Log Level"))
        self.logDirectoryLabel.setText(self.tr("Log Directory"))
        self.logDirectoryBrowse.setText(self.tr("Browse"))
        self.logDirectoryBrowse.setToolTip(self.tr("Select Log Directory"))
        self.logFileLabel.setText(self.tr("Log File Name"))
        self.logFileEdit.setPlaceholderText(self.tr("e.g. system.log"))
        self.logMaxSizeLabel.setText(self.tr("Max Log Size"))
        self.logMaxSizeSuffix.setText(self.tr("MB"))
        self.logBackupLabel.setText(self.tr("Backup Files"))
        self.logConsoleLabel.setText(self.tr("Enable Console Output"))
        self.logFormatLabel.setText(self.tr("Log Format"))
        self.logFormatEdit.setPlaceholderText(self.tr("Leave empty to use default format"))
        self.logDatefmtLabel.setText(self.tr("Date Format"))
        self.logDatefmtEdit.setPlaceholderText(self.tr("Leave empty to use default date format"))
        self.loggingHintLabel.setText(
            self.tr("Set size to 0 to disable rotation. Changes take effect immediately after saving.")
        )
        self.saveLoggingButton.setText(self.tr("Save Logging Settings"))


__all__ = ["PreferencesPage"]
