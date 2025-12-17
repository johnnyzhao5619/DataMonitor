# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import json
from urllib.parse import urlparse
import re

import configuration
import send_email


class MonitorItemDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor Item")
        self.setModal(True)
        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit()
        self.url_edit = QtWidgets.QLineEdit()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["GET", "POST", "SERVER"])
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["HTTP", "JSON", "XML"])
        self.interval_spin = QtWidgets.QSpinBox()
        self.interval_spin.setRange(10, 86400)
        self.email_edit = QtWidgets.QLineEdit()
        self.payload_edit = QtWidgets.QPlainTextEdit()
        self.headers_edit = QtWidgets.QPlainTextEdit()

        layout.addRow("Name*", self.name_edit)
        layout.addRow("URL*", self.url_edit)
        layout.addRow("Type*", self.type_combo)
        layout.addRow("Format*", self.format_combo)
        layout.addRow("Interval(s)*", self.interval_spin)
        layout.addRow("Email*", self.email_edit)
        layout.addRow("Payload(JSON)", self.payload_edit)
        layout.addRow("Headers(JSON)", self.headers_edit)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        if data:
            self.name_edit.setText(data.get("name", ""))
            self.url_edit.setText(data.get("url", ""))
            self.type_combo.setCurrentText(data.get("type", "GET"))
            self.format_combo.setCurrentText(data.get("format", "HTTP"))
            self.interval_spin.setValue(int(data.get("interval", 60)))
            self.email_edit.setText(data.get("email", ""))
            self.payload_edit.setPlainText(data.get("payload", ""))
            headers = data.get("headers", {})
            self.headers_edit.setPlainText(json.dumps(headers) if headers else "")

    def _on_accept(self):
        try:
            self.get_data()
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.warning(self, "Validation Failed", str(exc))
            return
        self.accept()

    def get_data(self):
        headers_txt = self.headers_edit.toPlainText().strip()
        payload_txt = self.payload_edit.toPlainText().strip()
        headers = {}
        payload = ""
        if headers_txt:
            try:
                headers = json.loads(headers_txt)
            except Exception as exc:
                raise ValueError(f"Headers JSON is invalid: {exc}")
        if payload_txt:
            payload = payload_txt
            if self.type_combo.currentText() == "POST":
                try:
                    json.loads(payload_txt)
                except Exception as exc:
                        raise ValueError(f"Payload JSON is invalid: {exc}")

        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        email = self.email_edit.text().strip()
        if not name or not url or not email:
            raise ValueError("Name / URL / Email is required")
        parsed = urlparse(url if url.startswith(("http://", "https://")) else "http://" + url)
        if not parsed.hostname:
            raise ValueError("URL is missing a hostname")
        if "@" not in email:
            raise ValueError("Email format is invalid")
        return {
            "name": name,
            "url": url,
            "type": self.type_combo.currentText(),
            "format": self.format_combo.currentText(),
            "interval": str(self.interval_spin.value()),
            "email": email,
            "payload": payload,
            "headers": headers,
        }


class ConfigDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(800, 600)
        self.setModal(True)
        self.tabs = QtWidgets.QTabWidget(self)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tabs)

        self.general_tab = QtWidgets.QWidget()
        self.mail_tab = QtWidgets.QWidget()
        self.templates_tab = QtWidgets.QWidget()
        self.monitor_tab = QtWidgets.QWidget()

        self._build_general_tab()
        self._build_mail_tab()
        self._build_templates_tab()
        self._build_monitor_tab()

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
            | QtWidgets.QDialogButtonBox.Apply)
        btn_box.accepted.connect(self.save_and_close)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(
            self.save_only)
        main_layout.addWidget(btn_box)

        self.load_data()
        # Default to monitor tab for quicker access to frequent operations
        self.tabs.setCurrentWidget(self.monitor_tab)

    # Tabs builders
    def _build_general_tab(self):
        layout = QtWidgets.QFormLayout(self.general_tab)
        self.app_name_edit = QtWidgets.QLineEdit()
        self.version_edit = QtWidgets.QLineEdit()
        self.version_edit.setReadOnly(True)
        self.timezone_spin = QtWidgets.QSpinBox()
        self.timezone_spin.setRange(-12, 14)
        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["debug", "info", "warning", "error"])
        layout.addRow("App Name", self.app_name_edit)
        layout.addRow("Version", self.version_edit)
        layout.addRow("Timezone", self.timezone_spin)
        layout.addRow("Log Level", self.log_level_combo)
        self.tabs.addTab(self.general_tab, "General")

    def _build_mail_tab(self):
        layout = QtWidgets.QFormLayout(self.mail_tab)
        self.smtp_server_edit = QtWidgets.QLineEdit()
        self.smtp_port_spin = QtWidgets.QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.from_addr_edit = QtWidgets.QLineEdit()
        self.test_to_edit = QtWidgets.QLineEdit()
        self.test_btn = QtWidgets.QPushButton("Send Test")
        self.test_btn.clicked.connect(self.send_test_mail)
        layout.addRow("SMTP Server", self.smtp_server_edit)
        layout.addRow("SMTP Port", self.smtp_port_spin)
        layout.addRow("Username", self.username_edit)
        layout.addRow("Password", self.password_edit)
        layout.addRow("From", self.from_addr_edit)
        layout.addRow("Test To", self.test_to_edit)
        layout.addRow(self.test_btn)
        self.tabs.addTab(self.mail_tab, "Mail")

    def _build_templates_tab(self):
        layout = QtWidgets.QFormLayout(self.templates_tab)
        mono = QtGui.QFont("Consolas" if QtGui.QFont("Consolas").family() else "", 9)
        self.outage_subject = QtWidgets.QLineEdit()
        self.outage_body = QtWidgets.QPlainTextEdit()
        self.restored_subject = QtWidgets.QLineEdit()
        self.restored_body = QtWidgets.QPlainTextEdit()
        self.log_line = QtWidgets.QPlainTextEdit()
        for w in (self.outage_body, self.restored_body, self.log_line):
            w.setFont(mono)
            w.setMinimumHeight(60)
        layout.addRow("Outage Subject", self.outage_subject)
        layout.addRow("Outage Body", self.outage_body)
        layout.addRow("Restored Subject", self.restored_subject)
        layout.addRow("Restored Body", self.restored_body)
        layout.addRow("Log Line", self.log_line)
        hint = QtWidgets.QLabel(
            "Available placeholders: {service_name}, {timestamp}, {remark}, {time}, {timezone}")
        layout.addRow(hint)
        self.preview_btn = QtWidgets.QPushButton("Preview Outage")
        self.preview_btn.clicked.connect(self.preview_template)
        layout.addRow(self.preview_btn)
        self.tabs.addTab(self.templates_tab, "Templates")

    def _build_monitor_tab(self):
        vbox = QtWidgets.QVBoxLayout(self.monitor_tab)
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Name", "URL", "Type", "Format", "Interval", "Email", "Headers"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        vbox.addWidget(self.table)
        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add")
        self.edit_btn = QtWidgets.QPushButton("Edit")
        self.del_btn = QtWidgets.QPushButton("Delete")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch(1)
        vbox.addLayout(btn_layout)
        self.tabs.addTab(self.monitor_tab, "Monitor List")

        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn.clicked.connect(self.edit_item)
        self.del_btn.clicked.connect(self.delete_item)

    # Data handling
    def load_data(self):
        app, ver = configuration.read_general()
        self.app_name_edit.setText(app)
        self.version_edit.setText(ver)
        self.timezone_spin.setValue(int(configuration.get_timezone()))
        try:
            cfg = configuration._read_config('Config.ini')
            log_level = cfg.get('Logging', 'log_level', fallback='info')
        except Exception:
            log_level = 'info'
        idx = self.log_level_combo.findText(log_level)
        if idx >= 0:
            self.log_level_combo.setCurrentIndex(idx)

        mail = configuration.read_mail_configuration()
        self.smtp_server_edit.setText(mail.get('smtp_server', ''))
        self.smtp_port_spin.setValue(int(mail.get('smtp_port', 25)))
        self.username_edit.setText(mail.get('username', ''))
        self.password_edit.setText(mail.get('password', ''))
        self.from_addr_edit.setText(mail.get('from_addr', ''))

        self.outage_subject.setText(configuration.get_template(
            'outage_subject',
            "{timestamp}: {service_name} outage detected"))
        self.outage_body.setPlainText(configuration.get_template(
            'outage_body',
            "{service_name} is unreachable at {timestamp}. Remark: {remark}"))
        self.restored_subject.setText(configuration.get_template(
            'restored_subject',
            "{timestamp}: {service_name} restored"))
        self.restored_body.setPlainText(configuration.get_template(
            'restored_body',
            "{service_name} recovered at {timestamp}. Remark: {remark}"))
        self.log_line.setPlainText(configuration.get_template(
            'log_line',
            ">>{time} (Timezone: {timezone})\n>>Action:{action}\n{log}\n"))

        self._load_monitor_table()

    def _validate_email(self, email: str) -> bool:
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

    def send_test_mail(self):
        to_addr = self.test_to_edit.text().strip()
        if not to_addr or not self._validate_email(to_addr):
            QtWidgets.QMessageBox.warning(self, "Test Mail",
                                          "Please enter a valid test email")
            return
        mail = {
            'smtp_server': self.smtp_server_edit.text().strip(),
            'smtp_port': str(self.smtp_port_spin.value()),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip(),
            'from_addr': self.from_addr_edit.text().strip(),
        }
        try:
            subject = self.outage_subject.text().strip() or "Test Mail"
            body = self.outage_body.toPlainText().strip() or "Test Body"
            send_email.send_email(subject, body, to_addr)
            QtWidgets.QMessageBox.information(self, "Test Mail", "Sent successfully (check inbox)")
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Test Mail Failed", str(exc))

    def _load_monitor_table(self):
        monitors = configuration.read_monitor_list()
        self.table.setRowCount(len(monitors))
        for r, item in enumerate(monitors):
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(item['name']))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(item['url']))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(item['type']))
            self.table.setItem(r, 3,
                               QtWidgets.QTableWidgetItem(item['format']))
            self.table.setItem(r, 4,
                               QtWidgets.QTableWidgetItem(item['interval']))
            self.table.setItem(r, 5, QtWidgets.QTableWidgetItem(item['email']))
            headers = item.get('headers') or {}
            self.table.setItem(r, 6,
                               QtWidgets.QTableWidgetItem(json.dumps(headers)))

    def _collect_monitor_table(self):
        rows = self.table.rowCount()
        monitors = []
        for r in range(rows):
            try:
                monitors.append({
                    'name': self.table.item(r, 0).text(),
                    'url': self.table.item(r, 1).text(),
                    'type': self.table.item(r, 2).text(),
                    'format': self.table.item(r, 3).text(),
                    'interval': self.table.item(r, 4).text(),
                    'email': self.table.item(r, 5).text(),
                    'payload': '',
                    'headers': json.loads(self.table.item(r, 6).text() or "{}")
                })
            except Exception as exc:
                raise ValueError(f"Failed to parse row {r+1}: {exc}")
        return monitors

    # CRUD handlers
    def add_item(self):
        dlg = MonitorItemDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            data = dlg.get_data()
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(data['name']))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(data['url']))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(data['type']))
            self.table.setItem(r, 3,
                               QtWidgets.QTableWidgetItem(data['format']))
            self.table.setItem(r, 4,
                               QtWidgets.QTableWidgetItem(data['interval']))
            self.table.setItem(r, 5, QtWidgets.QTableWidgetItem(data['email']))
            self.table.setItem(r, 6,
                               QtWidgets.QTableWidgetItem(
                                   json.dumps(data['headers'])))

    def edit_item(self):
        row = self.table.currentRow()
        if row < 0:
            return
        data = {
            'name': self.table.item(row, 0).text(),
            'url': self.table.item(row, 1).text(),
            'type': self.table.item(row, 2).text(),
            'format': self.table.item(row, 3).text(),
            'interval': self.table.item(row, 4).text(),
            'email': self.table.item(row, 5).text(),
            'headers': json.loads(self.table.item(row, 6).text() or "{}"),
            'payload': ''
        }
        dlg = MonitorItemDialog(self, data)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            data = dlg.get_data()
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(data['name']))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(data['url']))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(data['type']))
            self.table.setItem(row, 3,
                               QtWidgets.QTableWidgetItem(data['format']))
            self.table.setItem(row, 4,
                               QtWidgets.QTableWidgetItem(data['interval']))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(data['email']))
            self.table.setItem(row, 6,
                               QtWidgets.QTableWidgetItem(
                                   json.dumps(data['headers'])))

    def delete_item(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def preview_template(self):
        ctx = {
            'service_name': 'DemoService',
            'timestamp': '2025-01-01 12:00:00',
            'remark': 'Sample remark',
            'time': '2025-01-01 12:00:00',
            'timezone': '0'
        }
        try:
            subject = (self.outage_subject.text().strip() or "").format(**ctx)
            body = (self.outage_body.toPlainText().strip() or "").format(**ctx)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.warning(self, "Preview Failed", str(exc))
            return
        msg = f"Subject:\n{subject}\n\nBody:\n{body}"
        QtWidgets.QMessageBox.information(self, "Outage Preview", msg)

    # Save
    def save_only(self):
        self._save()

    def save_and_close(self):
        if self._save():
            self.accept()

    def _save(self):
        try:
            configuration.save_general(self.app_name_edit.text().strip(),
                                       self.version_edit.text().strip(),
                                       str(self.timezone_spin.value()),
                                       self.log_level_combo.currentText())
            configuration.save_mail(
                smtp_server=self.smtp_server_edit.text().strip(),
                smtp_port=str(self.smtp_port_spin.value()),
                username=self.username_edit.text().strip(),
                password=self.password_edit.text().strip(),
                from_addr=self.from_addr_edit.text().strip())
            configuration.save_templates(
                outage_subject=self.outage_subject.text().strip(),
                outage_body=self.outage_body.toPlainText().strip(),
                restored_subject=self.restored_subject.text().strip(),
                restored_body=self.restored_body.toPlainText().strip(),
                log_line=self.log_line.toPlainText())
            configuration.save_monitor_list(self._collect_monitor_table())
            return True
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Save Failed", str(exc))
            return False
