"""Preferences page view containing runtime and display settings."""
from __future__ import annotations

from PyQt5 import QtWidgets


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

        layout.addStretch(1)

    def retranslate_ui(self) -> None:
        self.timezoneHeading.setText(self.tr("Runtime Information"))
        self.locationButton.setText(self.tr("Set Timezone"))
        self.themeLabel.setText(self.tr("Theme"))
        self.themeSelector.setToolTip(self.tr("Select Theme"))
        self.languageLabel.setText(self.tr("Language"))
        self.languageSelector.setToolTip(self.tr("Select Language"))


__all__ = ["PreferencesPage"]
