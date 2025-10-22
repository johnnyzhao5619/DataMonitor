"""主界面与配置向导 UI。"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict
from typing import Dict, Iterable, List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

import configuration
import sendEmail


BASE_STYLESHEET = """
QMainWindow {
    background-color: #F3F2F1;
}
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #201F1E;
}
QPushButton {
    background-color: #6264A7;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}
QPushButton[category="navigation"] {
    background-color: transparent;
    color: #201F1E;
    border-radius: 8px;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
}
QPushButton[category="navigation"]:hover {
    background-color: #E1DFDD;
    color: #201F1E;
}
QPushButton[category="navigation"]:checked {
    background-color: #C8C6C4;
    color: #201F1E;
}
QPushButton:pressed {
    background-color: #33344A;
}
QPushButton:disabled {
    background-color: #E1DFDD;
    color: #A19F9D;
}
QFrame#navigationBar {
    background-color: #F3F2F1;
    border-right: 1px solid #E1DFDD;
}
QFrame[role="card"], QWidget[role="card"] {
    background: white;
    border: 1px solid #E1DFDD;
    border-radius: 10px;
}
QFrame[role="card"] QLabel[role="cardTitle"], QWidget[role="card"] QLabel[role="cardTitle"] {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
QLabel[role="heading"] {
    font-size: 18px;
    font-weight: 600;
}
QLabel[role="hint"] {
    color: #605E5C;
}
QLabel[role="error"] {
    color: #C50F1F;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    background: white;
    border: 1px solid #C8C6C4;
    border-radius: 6px;
    padding: 6px;
}
QListWidget {
    background: white;
    border: 1px solid #C8C6C4;
    border-radius: 6px;
}
QStatusBar {
    background: #E1DFDD;
    border-top: 1px solid #C8C6C4;
}
QTabWidget::pane {
    border: 1px solid #C8C6C4;
    border-radius: 6px;
}
QTabBar::tab {
    background: #E9E9F0;
    border: 1px solid #C8C6C4;
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: white;
    color: #201F1E;
}
"""


class NavigationBar(QtWidgets.QFrame):
    """遵循 Teams 视觉规范的侧边导航栏。"""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationBar")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Monitor Center")
        title.setAlignment(QtCore.Qt.AlignHCenter)
        title.setProperty("role", "heading")
        layout.addWidget(title)

        layout.addSpacing(12)

        self.monitorButton = self._create_button("监控 Monitor", checkable=True)
        self.configButton = self._create_button("配置 Configuration", checkable=True)

        layout.addWidget(self.monitorButton)
        layout.addWidget(self.configButton)

        layout.addStretch(1)

        self.locationButton = self._create_button("时区 Time Zone", checkable=False)
        layout.addWidget(self.locationButton)

    def set_active(self, button: QtWidgets.QPushButton) -> None:
        for item in self._iter_nav_buttons():
            if item.isCheckable():
                item.setChecked(item is button)

    def _iter_nav_buttons(self) -> Iterable[QtWidgets.QPushButton]:
        return (self.monitorButton, self.configButton, self.locationButton)

    def _create_button(self, text: str, *, checkable: bool) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(text)
        button.setCheckable(checkable)
        button.setProperty("category", "navigation")
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        return button


class MonitorDashboard(QtWidgets.QWidget):
    """监控信息仪表盘。"""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(16)
        layout.addLayout(cards_row)

        self.localTimeGroupBox = QtWidgets.QGroupBox("本地时间 Local Time")
        self.localTimeGroupBox.setProperty("role", "card")
        local_layout = QtWidgets.QVBoxLayout(self.localTimeGroupBox)
        local_layout.setContentsMargins(16, 20, 16, 16)

        self.localTimeLabel = QtWidgets.QLabel("2023-01-01 00:00:00")
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.localTimeLabel.setFont(font)
        local_layout.addWidget(self.localTimeLabel)

        self.utcTimeGroupBox = QtWidgets.QGroupBox("UTC时间 UTC Time")
        self.utcTimeGroupBox.setProperty("role", "card")
        utc_layout = QtWidgets.QVBoxLayout(self.utcTimeGroupBox)
        utc_layout.setContentsMargins(16, 20, 16, 16)

        self.utcTimeLabel = QtWidgets.QLabel("2023-01-01 00:00:00")
        self.utcTimeLabel.setFont(font)
        utc_layout.addWidget(self.utcTimeLabel)

        cards_row.addWidget(self.localTimeGroupBox, 1)
        cards_row.addWidget(self.utcTimeGroupBox, 1)

        self.logCard = QtWidgets.QFrame()
        self.logCard.setProperty("role", "card")
        log_layout = QtWidgets.QVBoxLayout(self.logCard)
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(12)

        log_title = QtWidgets.QLabel("实时日志 Live Feed")
        log_title.setProperty("role", "cardTitle")
        log_layout.addWidget(log_title)

        self.monitorBrowser = QtWidgets.QTextBrowser()
        self.monitorBrowser.setMinimumHeight(320)
        log_layout.addWidget(self.monitorBrowser)

        layout.addWidget(self.logCard, 1)


class ConfigurationWorkspace(QtWidgets.QWidget):
    """承载配置向导的卡片化工作区。"""

    def __init__(self, config_wizard: QtWidgets.QWidget, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QtWidgets.QFrame()
        card.setProperty("role", "card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(0)
        card_layout.addWidget(config_wizard)

        layout.addWidget(card)


class MainWindowUI(QtCore.QObject):
    """负责搭建主界面布局，并暴露关键控件。"""

    monitor_view_index = 0
    config_view_index = 1

    def __init__(self) -> None:
        super().__init__()
        self.central_widget: Optional[QtWidgets.QWidget] = None
        self.switchButton: QtWidgets.QPushButton
        self.configButton: QtWidgets.QPushButton
        self.locationButton: QtWidgets.QPushButton
        self.localTimeGroupBox: QtWidgets.QGroupBox
        self.localTimeLabel: QtWidgets.QLabel
        self.utcTimeGroupBox: QtWidgets.QGroupBox
        self.utcTimeLabel: QtWidgets.QLabel
        self.monitorBrowser: QtWidgets.QTextBrowser
        self.contentStack: QtWidgets.QStackedWidget
        self.configWizard: ConfigWizard

    def setup_ui(self, window: QtWidgets.QMainWindow) -> None:
        window.resize(1080, 700)
        window.setMinimumSize(920, 600)
        window.setStyleSheet(BASE_STYLESHEET)

        self.central_widget = QtWidgets.QWidget(window)
        self.central_widget.setObjectName("centralWidget")
        window.setCentralWidget(self.central_widget)

        shell_layout = QtWidgets.QHBoxLayout(self.central_widget)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.navigationBar = NavigationBar()
        shell_layout.addWidget(self.navigationBar, 0)

        content_container = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        shell_layout.addWidget(content_container, 1)

        self.contentStack = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.contentStack, 1)

        # 监控视图
        monitor_page = MonitorDashboard()
        self.contentStack.addWidget(monitor_page)

        # 配置视图
        self.configWizard = ConfigWizard()
        configuration_page = ConfigurationWorkspace(self.configWizard)
        self.contentStack.addWidget(configuration_page)

        self.switchButton = self.navigationBar.monitorButton
        self.configButton = self.navigationBar.configButton
        self.locationButton = self.navigationBar.locationButton

        self.localTimeGroupBox = monitor_page.localTimeGroupBox
        self.localTimeLabel = monitor_page.localTimeLabel
        self.utcTimeGroupBox = monitor_page.utcTimeGroupBox
        self.utcTimeLabel = monitor_page.utcTimeLabel
        self.monitorBrowser = monitor_page.monitorBrowser

        self.show_monitor_page()

    # 导航方法
    def show_monitor_page(self) -> None:
        self.contentStack.setCurrentIndex(self.monitor_view_index)
        self.navigationBar.set_active(self.switchButton)

    def show_configuration_page(self) -> None:
        self.contentStack.setCurrentIndex(self.config_view_index)
        self.navigationBar.set_active(self.configButton)


class ConfigWizard(QtWidgets.QWidget):
    """配置界面，负责展示与编辑监控项。"""

    monitorsSaved = QtCore.pyqtSignal(list)
    requestReload = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._monitors: List[Dict[str, object]] = []
        self._payload_error: Optional[str] = None
        self._headers_error: Optional[str] = None
        self._is_updating_form = False

        self._build_ui()

    # UI 构建
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("配置向导 Configuration Wizard")
        title.setProperty("role", "heading")
        layout.addWidget(title)

        hint = QtWidgets.QLabel("在左侧选择监控项，可新增、删除或修改配置，保存后立即写入配置文件。")
        hint.setWordWrap(True)
        hint.setProperty("role", "hint")
        layout.addWidget(hint)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(16)
        layout.addLayout(content_layout, 1)

        list_container = QtWidgets.QVBoxLayout()
        list_container.setSpacing(8)
        self.monitorList = QtWidgets.QListWidget()
        self.monitorList.currentRowChanged.connect(self._on_current_row_changed)
        list_container.addWidget(self.monitorList, 1)

        list_button_layout = QtWidgets.QHBoxLayout()
        list_button_layout.setSpacing(8)
        self.addButton = QtWidgets.QPushButton("新增")
        self.addButton.clicked.connect(self._add_monitor)
        self.removeButton = QtWidgets.QPushButton("删除")
        self.removeButton.clicked.connect(self._remove_current_monitor)
        list_button_layout.addWidget(self.addButton)
        list_button_layout.addWidget(self.removeButton)
        list_container.addLayout(list_button_layout)

        content_layout.addLayout(list_container, 1)

        form_container = QtWidgets.QVBoxLayout()
        form_container.setSpacing(12)

        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(form_widget)
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        form_layout.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(12)

        self.nameEdit = QtWidgets.QLineEdit()
        self.nameEdit.textChanged.connect(self._on_form_changed)
        form_layout.addRow("名称 Name", self.nameEdit)

        self.urlEdit = QtWidgets.QLineEdit()
        self.urlEdit.textChanged.connect(self._on_form_changed)
        form_layout.addRow("地址 URL", self.urlEdit)

        self.typeCombo = QtWidgets.QComboBox()
        for monitor_type in sorted(configuration.SUPPORTED_MONITOR_TYPES):
            self.typeCombo.addItem(monitor_type)
        self.typeCombo.currentTextChanged.connect(self._on_form_changed)
        form_layout.addRow("类型 Type", self.typeCombo)

        self.intervalSpin = QtWidgets.QSpinBox()
        self.intervalSpin.setRange(5, 86400)
        self.intervalSpin.setSuffix(" 秒")
        self.intervalSpin.valueChanged.connect(self._on_form_changed)
        form_layout.addRow("周期 Interval", self.intervalSpin)

        self.emailEdit = QtWidgets.QLineEdit()
        self.emailEdit.setPlaceholderText("可选，支持逗号分隔多个邮箱")
        self.emailEdit.textChanged.connect(self._on_form_changed)
        form_layout.addRow("通知邮箱", self.emailEdit)

        self.payloadEdit = QtWidgets.QPlainTextEdit()
        self.payloadEdit.setPlaceholderText("可选，JSON 或 key=value 格式")
        self.payloadEdit.textChanged.connect(self._on_form_changed)
        self.payloadEdit.setFixedHeight(80)
        form_layout.addRow("Payload", self.payloadEdit)

        self.headersEdit = QtWidgets.QPlainTextEdit()
        self.headersEdit.setPlaceholderText("可选，JSON 或 key=value 格式")
        self.headersEdit.textChanged.connect(self._on_form_changed)
        self.headersEdit.setFixedHeight(80)
        form_layout.addRow("Headers", self.headersEdit)

        form_container.addWidget(form_widget)

        self.validationLabel = QtWidgets.QLabel()
        self.validationLabel.setProperty("role", "error")
        self.validationLabel.setWordWrap(True)
        form_container.addWidget(self.validationLabel)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        self.saveButton = QtWidgets.QPushButton("保存")
        self.saveButton.clicked.connect(self._emit_save)
        self.revertButton = QtWidgets.QPushButton("恢复配置")
        self.revertButton.clicked.connect(self.requestReload.emit)
        button_layout.addWidget(self.revertButton)
        button_layout.addWidget(self.saveButton)
        form_container.addLayout(button_layout)

        preview_group = QtWidgets.QGroupBox("通知预览 Notification Preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(12, 16, 12, 12)
        self.previewTabs = QtWidgets.QTabWidget()
        self.alertPreview = QtWidgets.QPlainTextEdit()
        self.alertPreview.setReadOnly(True)
        self.recoveryPreview = QtWidgets.QPlainTextEdit()
        self.recoveryPreview.setReadOnly(True)
        self.previewTabs.addTab(self.alertPreview, "告警 Alert")
        self.previewTabs.addTab(self.recoveryPreview, "恢复 Recovery")
        preview_layout.addWidget(self.previewTabs)
        form_container.addWidget(preview_group, 1)

        content_layout.addLayout(form_container, 2)

        self._set_form_enabled(False)
        self._update_validation_state()

    # 数据交互
    def load_monitors(self, monitors: List[Dict[str, object]]) -> None:
        self._monitors = []
        for item in monitors:
            if isinstance(item, configuration.MonitorItem):
                data = asdict(item)
            elif hasattr(item, "get"):
                data = item  # type: ignore[assignment]
            else:
                data = {
                    "name": getattr(item, "name", ""),
                    "url": getattr(item, "url", ""),
                    "type": getattr(item, "type", getattr(item, "monitor_type", "")),
                    "interval": getattr(item, "interval", 60),
                    "email": getattr(item, "email", ""),
                    "payload": getattr(item, "payload", None),
                    "headers": getattr(item, "headers", None),
                }

            type_value = data.get("type") or data.get("monitor_type") or ""
            interval_value = data.get("interval", 60)
            if interval_value is None:
                interval_value = 60
            email_value = data.get("email")
            record = {
                "name": str(data.get("name", "")),
                "url": str(data.get("url", "")),
                "type": str(type_value).upper(),
                "interval": int(interval_value),
                "email": "" if email_value is None else str(email_value),
                "payload": data.get("payload"),
                "headers": data.get("headers"),
            }
            record["_payload_text"] = self._serialise_mapping(record.get("payload"))
            record["_headers_text"] = self._serialise_mapping(record.get("headers"))
            self._monitors.append(record)

        self._refresh_list()
        has_items = bool(self._monitors)
        self._set_form_enabled(has_items)
        if has_items:
            self.monitorList.setCurrentRow(0)
        else:
            self._clear_form()
        self._update_validation_state()

    def get_monitors(self) -> List[Dict[str, object]]:
        result: List[Dict[str, object]] = []
        for record in self._monitors:
            payload = self._parse_optional_mapping(record.get("_payload_text", ""))
            headers = self._parse_optional_mapping(record.get("_headers_text", ""))
            item = {
                "name": record.get("name", ""),
                "url": record.get("url", ""),
                "type": record.get("type", ""),
                "interval": int(record.get("interval", 60)),
                "email": record.get("email", ""),
            }
            if payload is not None:
                item["payload"] = payload
            if headers is not None:
                item["headers"] = headers
            result.append(item)
        return result

    # 列表维护
    def _refresh_list(self) -> None:
        self.monitorList.blockSignals(True)
        self.monitorList.clear()
        for record in self._monitors:
            title = self._format_item_title(record)
            self.monitorList.addItem(title)
        self.monitorList.blockSignals(False)

    def _format_item_title(self, record: Dict[str, object]) -> str:
        name = record.get("name") or "(未命名)"
        mtype = record.get("type") or "?"
        return f"{name} [{mtype}]"

    def _add_monitor(self) -> None:
        new_record = {
            "name": "新监控项",
            "url": "http://",
            "type": next(iter(sorted(configuration.SUPPORTED_MONITOR_TYPES))),
            "interval": 60,
            "email": "",
            "payload": None,
            "headers": None,
            "_payload_text": "",
            "_headers_text": "",
        }
        self._monitors.append(new_record)
        self._refresh_list()
        self.monitorList.setCurrentRow(len(self._monitors) - 1)
        self._set_form_enabled(True)
        self._update_validation_state()

    def _remove_current_monitor(self) -> None:
        row = self.monitorList.currentRow()
        if row < 0 or row >= len(self._monitors):
            return
        del self._monitors[row]
        self._refresh_list()
        if self._monitors:
            self.monitorList.setCurrentRow(min(row, len(self._monitors) - 1))
        else:
            self._clear_form()
            self._set_form_enabled(False)
        self._update_validation_state()

    # 表单交互
    def _clear_form(self) -> None:
        self._is_updating_form = True
        try:
            self.nameEdit.clear()
            self.urlEdit.clear()
            self.typeCombo.setCurrentIndex(0)
            self.intervalSpin.setValue(60)
            self.emailEdit.clear()
            self.payloadEdit.clear()
            self.headersEdit.clear()
            self.alertPreview.clear()
            self.recoveryPreview.clear()
        finally:
            self._is_updating_form = False

    def _set_form_enabled(self, enabled: bool) -> None:
        for widget in (
            self.nameEdit,
            self.urlEdit,
            self.typeCombo,
            self.intervalSpin,
            self.emailEdit,
            self.payloadEdit,
            self.headersEdit,
            self.saveButton,
        ):
            widget.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)

    def _on_current_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._monitors):
            self._clear_form()
            return
        record = self._monitors[row]
        self._is_updating_form = True
        try:
            self.nameEdit.setText(record.get("name", ""))
            self.urlEdit.setText(record.get("url", ""))
            type_value = record.get("type", "")
            index = max(self.typeCombo.findText(type_value), 0)
            self.typeCombo.setCurrentIndex(index)
            self.intervalSpin.setValue(int(record.get("interval", 60)))
            self.emailEdit.setText(record.get("email", ""))
            self.payloadEdit.setPlainText(record.get("_payload_text", ""))
            self.headersEdit.setPlainText(record.get("_headers_text", ""))
        finally:
            self._is_updating_form = False
        self._payload_error = None
        self._headers_error = None
        self._update_preview()
        self._update_validation_state()

    def _on_form_changed(self) -> None:
        if self._is_updating_form:
            return
        row = self.monitorList.currentRow()
        if row < 0 or row >= len(self._monitors):
            return
        record = self._monitors[row]
        record["name"] = self.nameEdit.text().strip()
        record["url"] = self.urlEdit.text().strip()
        record["type"] = self.typeCombo.currentText().strip().upper()
        record["interval"] = int(self.intervalSpin.value())
        record["email"] = self.emailEdit.text().strip()
        record["_payload_text"] = self.payloadEdit.toPlainText().strip()
        record["_headers_text"] = self.headersEdit.toPlainText().strip()

        self._payload_error = self._validate_mapping_text(record["_payload_text"], "Payload")
        self._headers_error = self._validate_mapping_text(record["_headers_text"], "Headers")
        if self._payload_error is None:
            record["payload"] = self._parse_optional_mapping(record["_payload_text"])
        if self._headers_error is None:
            record["headers"] = self._parse_optional_mapping(record["_headers_text"])

        item = self.monitorList.item(row)
        if item is not None:
            item.setText(self._format_item_title(record))
        self._update_preview()
        self._update_validation_state()

    def _validate_mapping_text(self, text: str, label: str) -> Optional[str]:
        if not text:
            return None
        try:
            self._parse_optional_mapping(text)
        except ValueError as exc:
            return f"{label} 无法解析: {exc}"
        return None

    def _update_validation_state(self) -> None:
        errors: List[str] = []
        is_valid = True
        for index, record in enumerate(self._monitors, start=1):
            name = record.get("name", "").strip()
            url = record.get("url", "").strip()
            if not name:
                errors.append(f"监控项 {index} 名称不能为空")
            if not url:
                errors.append(f"监控项 {index} URL 不能为空")
            mtype = record.get("type", "").upper()
            if mtype not in configuration.SUPPORTED_MONITOR_TYPES:
                errors.append(f"监控项 {index} 类型必须为 {sorted(configuration.SUPPORTED_MONITOR_TYPES)} 之一")
            interval = int(record.get("interval", 0))
            if interval <= 0:
                errors.append(f"监控项 {index} 轮询周期必须大于 0")
            email = record.get("email", "").strip()
            if email and not self._validate_emails(email):
                errors.append(f"监控项 {index} 的通知邮箱格式不正确")
        if self._payload_error:
            errors.append(self._payload_error)
        if self._headers_error:
            errors.append(self._headers_error)

        is_valid = not errors
        self.saveButton.setEnabled(is_valid and bool(self._monitors))
        if errors:
            self.validationLabel.setText("\n".join(errors))
        else:
            self.validationLabel.clear()

    def _validate_emails(self, value: str) -> bool:
        for address in value.split(","):
            address = address.strip()
            if not address:
                continue
            if "@" not in address or address.startswith("@") or address.endswith("@"):
                return False
        return True

    def _update_preview(self) -> None:
        row = self.monitorList.currentRow()
        if row < 0 or row >= len(self._monitors):
            self.alertPreview.clear()
            self.recoveryPreview.clear()
            return
        record = self._monitors[row]
        now = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        service_name = record.get("name", "未命名服务") or "未命名服务"
        alert_subject, alert_body = sendEmail.build_outage_alert_message(service_name, now)
        recovery_subject, recovery_body = sendEmail.build_outage_recovery_message(service_name, now)
        alert_preview = f"Subject: {alert_subject}\n\n{alert_body}"
        recovery_preview = f"Subject: {recovery_subject}\n\n{recovery_body}"
        self.alertPreview.setPlainText(alert_preview)
        self.recoveryPreview.setPlainText(recovery_preview)

    def _emit_save(self) -> None:
        if not self.saveButton.isEnabled():
            return
        monitors = self.get_monitors()
        self.monitorsSaved.emit(monitors)

    # 工具方法
    def _parse_optional_mapping(self, text: str) -> Optional[Dict[str, object]]:
        if not text:
            return None
        return configuration.parse_mapping_string(text)

    def _serialise_mapping(self, value: Optional[Dict[str, object]]) -> str:
        if not value:
            return ""
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return ""

