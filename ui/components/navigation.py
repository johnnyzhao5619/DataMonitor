# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 12:05 a.m.
# @Author: John Zhao
"""Side navigation bar components."""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from PySide6 import QtCore, QtGui, QtWidgets

NAVIGATION_ORDER = ("monitor", "configuration", "preferences", "documentation",
                    "reports")
NAVIGATION_LABELS = {
    "monitor": "Monitor",
    "configuration": "Configuration",
    "preferences": "Preferences",
    "documentation": "Documentation",
    "reports": "Reports",
}


class NavigationBar(QtWidgets.QFrame):
    """Compact navigation bar used to switch primary views."""

    navigationTriggered = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationBar")

        self._button_group = QtWidgets.QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._handle_button_clicked)

        self._buttons: Dict[str, QtWidgets.QPushButton] = {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(16)

        self.titleLabel = QtWidgets.QLabel()
        self.titleLabel.setAlignment(QtCore.Qt.AlignHCenter)
        self.titleLabel.setProperty("role", "heading")
        layout.addWidget(self.titleLabel)

        layout.addSpacing(12)

        for nav_id in NAVIGATION_ORDER:
            button = self._create_nav_button(nav_id)
            layout.addWidget(button)
            setattr(self, f"{nav_id}Button", button)
            if nav_id == "configuration":
                self.configButton = button  # backward compatibility for legacy tests
            elif nav_id == "reports":
                self.reportButton = button  # expose singular alias used in tests

        layout.addStretch(1)

        self.retranslate_ui()

    # ------------------------------------------------------------------
    def buttons(self) -> Iterable[QtWidgets.QPushButton]:
        return self._buttons.values()

    def active_id(self) -> Optional[str]:
        for nav_id, button in self._buttons.items():
            if button.isChecked():
                return nav_id
        return None

    def set_active(self, nav_id: str) -> None:
        button = self._buttons.get(nav_id)
        if button is None:
            return
        was_blocked = button.blockSignals(True)
        button.setChecked(True)
        button.blockSignals(was_blocked)

    # ------------------------------------------------------------------
    def _create_nav_button(self, nav_id: str) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton()
        button.setObjectName(f"navButton_{nav_id}")
        button.setCheckable(True)
        button.setProperty("category", "navigation")
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._button_group.addButton(button)
        self._buttons[nav_id] = button
        return button

    def _handle_button_clicked(self,
                               button: QtWidgets.QAbstractButton) -> None:
        for nav_id, target in self._buttons.items():
            if target is button:
                self.navigationTriggered.emit(nav_id)
                break

    def retranslate_ui(self) -> None:
        self.titleLabel.setText(self.tr("Monitor Center"))
        for nav_id, button in self._buttons.items():
            label = NAVIGATION_LABELS.get(nav_id, nav_id.title())
            button.setText(self.tr(label))
