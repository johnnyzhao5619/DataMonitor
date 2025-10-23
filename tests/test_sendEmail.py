import logging
import smtplib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import configuration
import pytest


PROJECT_SMTP_CALLS = []


class DummySMTP:
    def __init__(self, host, port):
        assert isinstance(port, int)
        self.host = host
        self.port = port
        self.started_tls = False
        self.logged_in = False
        self.sent_messages = []

    def __enter__(self):
        PROJECT_SMTP_CALLS.append(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = True
        self.username = username
        self.password = password

    def sendmail(self, from_addr, to_addrs, message):
        self.sent_messages.append((from_addr, to_addrs, message))


def _patch_mail_configuration(monkeypatch, module, **overrides):
    base = {
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "username": "user",
        "password": "secret",
        "from_addr": "from@example.com",
        "to_addrs": "default@example.com",
    }
    base.update(overrides)
    monkeypatch.setattr(module.configuration, "read_mail_configuration", lambda: dict(base))


@pytest.fixture(autouse=True)
def reset_smtp_calls():
    PROJECT_SMTP_CALLS.clear()
    yield
    PROJECT_SMTP_CALLS.clear()


def test_send_email_prefers_explicit_recipients(monkeypatch):
    import sendEmail

    _patch_mail_configuration(monkeypatch, sendEmail)

    monkeypatch.setattr(sendEmail.smtplib, "SMTP", DummySMTP)

    sendEmail.send_email(
        "Subject",
        "Body",
        recipients="override1@example.com, override2@example.com",
    )

    assert PROJECT_SMTP_CALLS, "应该创建 SMTP 连接"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert smtp_instance.started_tls is True
    assert smtp_instance.logged_in is True

    assert len(smtp_instance.sent_messages) == 1
    from_addr, to_addrs, message = smtp_instance.sent_messages[0]
    assert from_addr == "from@example.com"
    assert to_addrs == ["override1@example.com", "override2@example.com"]
    assert "To: override1@example.com, override2@example.com" in message


def test_send_email_logs_authentication_error(monkeypatch, caplog):
    import sendEmail

    _patch_mail_configuration(monkeypatch, sendEmail)

    class AuthFailSMTP(DummySMTP):
        def login(self, username, password):  # noqa: D401 - 与父类签名保持一致
            raise smtplib.SMTPAuthenticationError(535, b"Auth failed")

    monkeypatch.setattr(sendEmail.smtplib, "SMTP", AuthFailSMTP)

    with caplog.at_level(logging.ERROR, logger="sendEmail"):
        with pytest.raises(smtplib.SMTPAuthenticationError):
            sendEmail.send_email("Subject", "Body")

    assert "SMTP 身份验证失败" in caplog.text
    assert "mail.smtp.authentication_error" in caplog.text


def test_send_email_logs_smtp_exception(monkeypatch, caplog):
    import sendEmail

    _patch_mail_configuration(monkeypatch, sendEmail)

    class SendFailSMTP(DummySMTP):
        def sendmail(self, from_addr, to_addrs, message):  # noqa: D401
            raise smtplib.SMTPException("send failed")

    monkeypatch.setattr(sendEmail.smtplib, "SMTP", SendFailSMTP)

    with caplog.at_level(logging.ERROR, logger="sendEmail"):
        with pytest.raises(smtplib.SMTPException):
            sendEmail.send_email("Subject", "Body")

    assert "SMTP 通信异常" in caplog.text
    assert "mail.smtp.communication_error" in caplog.text


def test_read_mail_configuration_bootstraps_placeholder(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    config_dir = tmp_path / "Config"
    config_file = config_dir / "Config.ini"

    assert not config_file.exists()

    values = configuration.read_mail_configuration()

    assert config_dir.is_dir()
    assert config_file.is_file()
    assert values == {
        "smtp_server": "<SMTP_SERVER>",
        "smtp_port": "<SMTP_PORT>",
        "username": "<USERNAME>",
        "password": "<PASSWORD>",
        "from_addr": "<FROM_ADDRESS>",
        "to_addrs": "<TO_ADDRESSES>",
    }
