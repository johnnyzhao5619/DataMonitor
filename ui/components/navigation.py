"""侧边导航栏组件。"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from PyQt5 import QtCore, QtGui, QtWidgets


class NavigationBar(QtWidgets.QFrame):
    """用于在主界面中切换视图的缩略导航栏。"""

    navigationTriggered = QtCore.pyqtSignal(str)

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

        self.monitorButton = self._create_nav_button("monitor")
        layout.addWidget(self.monitorButton)

        self.configButton = self._create_nav_button("configuration")
        layout.addWidget(self.configButton)

        self.reportButton = self._create_nav_button("reports")
        layout.addWidget(self.reportButton)

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

    def _handle_button_clicked(self, button: QtWidgets.QAbstractButton) -> None:
        for nav_id, target in self._buttons.items():
            if target is button:
                self.navigationTriggered.emit(nav_id)
                break

    def retranslate_ui(self) -> None:
        self.titleLabel.setText(self.tr("Monitor Center"))
        self.monitorButton.setText(self.tr("监控 Monitor"))
        self.configButton.setText(self.tr("配置 Configuration"))
        self.reportButton.setText(self.tr("报表 Reports"))
