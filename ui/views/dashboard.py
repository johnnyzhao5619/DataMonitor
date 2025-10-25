# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 12:05 a.m.
# @Author: John Zhao
"""Monitoring dashboard view."""
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class MonitorDashboard(QtWidgets.QWidget):
    """Dashboard displaying monitoring information."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(16)
        layout.addLayout(cards_row)

        self.localTimeGroupBox = QtWidgets.QGroupBox()
        self.localTimeGroupBox.setProperty("role", "card")
        local_layout = QtWidgets.QVBoxLayout(self.localTimeGroupBox)
        local_layout.setContentsMargins(16, 20, 16, 16)

        self.localTimeLabel = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.localTimeLabel.setFont(font)
        local_layout.addWidget(self.localTimeLabel)

        self.utcTimeGroupBox = QtWidgets.QGroupBox()
        self.utcTimeGroupBox.setProperty("role", "card")
        utc_layout = QtWidgets.QVBoxLayout(self.utcTimeGroupBox)
        utc_layout.setContentsMargins(16, 20, 16, 16)

        self.utcTimeLabel = QtWidgets.QLabel()
        self.utcTimeLabel.setFont(font)
        utc_layout.addWidget(self.utcTimeLabel)

        cards_row.addWidget(self.localTimeGroupBox, 1)
        cards_row.addWidget(self.utcTimeGroupBox, 1)

        self.logCard = QtWidgets.QFrame()
        self.logCard.setProperty("role", "card")
        log_layout = QtWidgets.QVBoxLayout(self.logCard)
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(12)

        self.logTitleLabel = QtWidgets.QLabel()
        self.logTitleLabel.setProperty("role", "cardTitle")
        log_layout.addWidget(self.logTitleLabel)

        self.monitorBrowser = QtWidgets.QTextBrowser()
        self.monitorBrowser.setObjectName("monitorBrowser")
        self.monitorBrowser.setMinimumHeight(320)
        log_layout.addWidget(self.monitorBrowser)

        layout.addWidget(self.logCard, 1)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.localTimeGroupBox.setTitle(self.tr("Local Time"))
        self.utcTimeGroupBox.setTitle(self.tr("UTC Time"))
        self.logTitleLabel.setText(self.tr("Live Feed"))
