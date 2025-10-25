"""配置向导视图组件。"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict
from typing import Dict, List, Optional
from urllib.parse import urlsplit

from PySide6 import QtCore, QtWidgets

import configuration
from monitoring import send_email


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
        self._config_wizard = config_wizard

    def retranslate_ui(self) -> None:
        if hasattr(self._config_wizard, "retranslate_ui"):
            self._config_wizard.retranslate_ui()


class ConfigWizard(QtWidgets.QWidget):
    """配置界面，负责展示与编辑监控项。"""

    monitorsSaved = QtCore.Signal(list)
    requestReload = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._monitors: List[Dict[str, object]] = []
        self._payload_error: Optional[str] = None
        self._headers_error: Optional[str] = None
        self._is_updating_form = False

        self._build_ui()
        self.retranslate_ui()

    # UI 构建
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        self.titleLabel = QtWidgets.QLabel()
        self.titleLabel.setProperty("role", "heading")
        layout.addWidget(self.titleLabel)

        self.hintLabel = QtWidgets.QLabel()
        self.hintLabel.setWordWrap(True)
        self.hintLabel.setProperty("role", "hint")
        layout.addWidget(self.hintLabel)

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
        self.addButton = QtWidgets.QPushButton()
        self.addButton.clicked.connect(self._add_monitor)
        self.removeButton = QtWidgets.QPushButton()
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
        self.nameLabel = QtWidgets.QLabel()
        form_layout.addRow(self.nameLabel, self.nameEdit)

        self.urlEdit = QtWidgets.QLineEdit()
        self.urlEdit.textChanged.connect(self._on_form_changed)
        self.urlLabel = QtWidgets.QLabel()
        form_layout.addRow(self.urlLabel, self.urlEdit)

        self.typeCombo = QtWidgets.QComboBox()
        for monitor_type in sorted(configuration.SUPPORTED_MONITOR_TYPES):
            self.typeCombo.addItem(monitor_type)
        self.typeCombo.currentTextChanged.connect(self._on_form_changed)
        self.typeLabel = QtWidgets.QLabel()
        form_layout.addRow(self.typeLabel, self.typeCombo)

        self.intervalSpin = QtWidgets.QSpinBox()
        self.intervalSpin.setRange(5, 86400)
        self.intervalSpin.valueChanged.connect(self._on_form_changed)
        self.intervalLabel = QtWidgets.QLabel()
        form_layout.addRow(self.intervalLabel, self.intervalSpin)

        self.emailEdit = QtWidgets.QLineEdit()
        self.emailEdit.textChanged.connect(self._on_form_changed)
        self.emailLabel = QtWidgets.QLabel()
        form_layout.addRow(self.emailLabel, self.emailEdit)

        self.payloadEdit = QtWidgets.QPlainTextEdit()
        self.payloadEdit.textChanged.connect(self._on_form_changed)
        self.payloadEdit.setFixedHeight(80)
        self.payloadLabel = QtWidgets.QLabel()
        form_layout.addRow(self.payloadLabel, self.payloadEdit)

        self.headersEdit = QtWidgets.QPlainTextEdit()
        self.headersEdit.textChanged.connect(self._on_form_changed)
        self.headersEdit.setFixedHeight(80)
        self.headersLabel = QtWidgets.QLabel()
        form_layout.addRow(self.headersLabel, self.headersEdit)

        form_container.addWidget(form_widget)

        self.validationLabel = QtWidgets.QLabel()
        self.validationLabel.setProperty("role", "error")
        self.validationLabel.setWordWrap(True)
        form_container.addWidget(self.validationLabel)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        self.saveButton = QtWidgets.QPushButton()
        self.saveButton.clicked.connect(self._emit_save)
        self.revertButton = QtWidgets.QPushButton()
        self.revertButton.clicked.connect(self.requestReload.emit)
        button_layout.addWidget(self.revertButton)
        button_layout.addWidget(self.saveButton)
        form_container.addLayout(button_layout)

        self.previewGroup = QtWidgets.QGroupBox()
        preview_layout = QtWidgets.QVBoxLayout(self.previewGroup)
        preview_layout.setContentsMargins(12, 16, 12, 12)
        self.previewTabs = QtWidgets.QTabWidget()
        self.alertPreview = QtWidgets.QPlainTextEdit()
        self.alertPreview.setReadOnly(True)
        self.recoveryPreview = QtWidgets.QPlainTextEdit()
        self.recoveryPreview.setReadOnly(True)
        self.previewTabs.addTab(self.alertPreview, "")
        self.previewTabs.addTab(self.recoveryPreview, "")
        preview_layout.addWidget(self.previewTabs)
        form_container.addWidget(self.previewGroup, 1)

        content_layout.addLayout(form_container, 2)

        self._set_form_enabled(False)
        self._update_validation_state()

    def retranslate_ui(self) -> None:
        self.titleLabel.setText(self.tr("配置向导 Configuration Wizard"))
        self.hintLabel.setText(
            self.tr("在左侧选择监控项，可新增、删除或修改配置，保存后立即写入配置文件。")
        )
        self.addButton.setText(self.tr("新增"))
        self.removeButton.setText(self.tr("删除"))
        self.nameLabel.setText(self.tr("名称 Name"))
        self.urlLabel.setText(self.tr("地址 URL"))
        self.urlEdit.setPlaceholderText(self.tr("请输入完整的服务地址，例如 https://example.com"))
        self.typeLabel.setText(self.tr("类型 Type"))
        self.intervalLabel.setText(self.tr("周期 Interval"))
        self.intervalSpin.setSuffix(self.tr(" 秒"))
        self.emailLabel.setText(self.tr("通知邮箱"))
        self.emailEdit.setPlaceholderText(self.tr("可选，支持逗号分隔多个邮箱"))
        self.payloadLabel.setText(self.tr("Payload"))
        self.payloadEdit.setPlaceholderText(self.tr("可选，JSON 或 key=value 格式"))
        self.headersLabel.setText(self.tr("Headers"))
        self.headersEdit.setPlaceholderText(self.tr("可选，JSON 或 key=value 格式"))
        self.saveButton.setText(self.tr("保存"))
        self.revertButton.setText(self.tr("恢复配置"))
        self.previewGroup.setTitle(self.tr("通知预览 Notification Preview"))
        self.previewTabs.setTabText(0, self.tr("告警 Alert"))
        self.previewTabs.setTabText(1, self.tr("恢复 Recovery"))

        current_row = self.monitorList.currentRow()
        self._refresh_list()
        if self.monitorList.count():
            if 0 <= current_row < self.monitorList.count():
                self.monitorList.setCurrentRow(current_row)
            else:
                self.monitorList.setCurrentRow(0)
        self._update_preview()
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
        name = record.get("name") or self.tr("(未命名)")
        mtype = record.get("type") or "?"
        return self.tr("{name} [{mtype}]").format(name=name, mtype=mtype)

    def _add_monitor(self) -> None:
        new_record = {
            "name": self.tr("新监控项"),
            "url": "",
            "type": next(iter(sorted(configuration.SUPPORTED_MONITOR_TYPES))),
            "interval": 60,
            "email": "",
            "payload": None,
            "headers": None,
            "_payload_text": "",
            "_headers_text": "",
        }
        self._monitors.append(new_record)
        self.monitorList.addItem(self._format_item_title(new_record))
        self.monitorList.setCurrentRow(self.monitorList.count() - 1)
        self._set_form_enabled(True)
        self._update_validation_state()

    def _remove_current_monitor(self) -> None:
        row = self.monitorList.currentRow()
        if row < 0 or row >= len(self._monitors):
            return
        self.monitorList.takeItem(row)
        del self._monitors[row]
        if self._monitors:
            self.monitorList.setCurrentRow(min(row, len(self._monitors) - 1))
        else:
            self._clear_form()
            self._set_form_enabled(False)
        self._update_validation_state()

    def _on_current_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._monitors):
            self._clear_form()
            self._set_form_enabled(False)
            return

        record = self._monitors[row]
        self._is_updating_form = True
        try:
            self.nameEdit.setText(record.get("name", ""))
            self.urlEdit.setText(record.get("url", ""))
            mtype = record.get("type", "")
            if mtype:
                index = self.typeCombo.findText(mtype, QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.typeCombo.setCurrentIndex(index)
            self.intervalSpin.setValue(int(record.get("interval", 60)))
            self.emailEdit.setText(record.get("email", ""))
            self.payloadEdit.setPlainText(record.get("_payload_text", ""))
            self.headersEdit.setPlainText(record.get("_headers_text", ""))
        finally:
            self._is_updating_form = False
        self._update_preview()

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
        finally:
            self._is_updating_form = False
        self._update_preview()

    def _set_form_enabled(self, enabled: bool) -> None:
        for widget in (
            self.monitorList,
            self.nameEdit,
            self.urlEdit,
            self.typeCombo,
            self.intervalSpin,
            self.emailEdit,
            self.payloadEdit,
            self.headersEdit,
            self.saveButton,
            self.revertButton,
            self.previewTabs,
        ):
            widget.setEnabled(enabled)

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

        self._payload_error = self._validate_mapping_text(
            record["_payload_text"], self.tr("Payload")
        )
        self._headers_error = self._validate_mapping_text(
            record["_headers_text"], self.tr("Headers")
        )
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
            return self.tr("{label} 无法解析: {error}").format(label=label, error=exc)
        return None

    def _update_validation_state(self) -> None:
        errors: List[str] = []
        for index, record in enumerate(self._monitors, start=1):
            name = record.get("name", "").strip()
            url = record.get("url", "").strip()
            if not name:
                errors.append(
                    self.tr("监控项 {index} 名称不能为空").format(index=index)
                )
            if not url:
                errors.append(
                    self.tr("监控项 {index} URL 不能为空").format(index=index)
                )
            elif not self._has_valid_hostname(url):
                errors.append(
                    self.tr("监控项 {index} URL 缺少有效的主机名").format(index=index)
                )
            mtype = record.get("type", "").upper()
            if mtype not in configuration.SUPPORTED_MONITOR_TYPES:
                allowed = ", ".join(sorted(configuration.SUPPORTED_MONITOR_TYPES))
                errors.append(
                    self.tr("监控项 {index} 类型必须为 {types} 之一").format(
                        index=index, types=allowed
                    )
                )
            interval = int(record.get("interval", 0))
            if interval <= 0:
                errors.append(
                    self.tr("监控项 {index} 轮询周期必须大于 0").format(index=index)
                )
            email = record.get("email", "").strip()
            if email and not self._validate_emails(email):
                errors.append(
                    self.tr("监控项 {index} 的通知邮箱格式不正确").format(index=index)
                )
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
        now = _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        service_name = record.get("name") or self.tr("未命名服务")
        alert_subject, alert_body = send_email.build_outage_alert_message(service_name, now)
        recovery_subject, recovery_body = send_email.build_outage_recovery_message(service_name, now)
        subject_prefix = self.tr("Subject")
        alert_preview = f"{subject_prefix}: {alert_subject}\n\n{alert_body}"
        recovery_preview = f"{subject_prefix}: {recovery_subject}\n\n{recovery_body}"
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

    def _has_valid_hostname(self, url: str) -> bool:
        target = url if "://" in url else f"http://{url}"
        parts = urlsplit(target)
        return bool(parts.hostname)
