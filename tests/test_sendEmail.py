import logging
import smtplib
import sys
import types
from email import message_from_string
from email.header import decode_header, make_header
from email.utils import getaddresses
from pathlib import Path

requests_stub = types.ModuleType("requests")
requests_stub.RequestException = Exception
requests_stub.Timeout = Exception
requests_stub.ConnectionError = Exception
requests_stub.get = None
requests_stub.post = None

sys.modules.setdefault("requests", requests_stub)

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


class DummySMTPSSL(DummySMTP):
    pass


def _patch_mail_configuration(monkeypatch, module, **overrides):
    base = {
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "username": "user",
        "password": "secret",
        "from_addr": "from@example.com",
        "to_addrs": "default@example.com",
        "use_starttls": True,
        "use_ssl": False,
    }
    base.update(overrides)
    monkeypatch.setattr(module.configuration, "read_mail_configuration",
                        lambda: dict(base))


@pytest.fixture(autouse=True)
def reset_smtp_calls():
    PROJECT_SMTP_CALLS.clear()
    yield
    PROJECT_SMTP_CALLS.clear()


def test_send_email_prefers_explicit_recipients(monkeypatch):
    from monitoring import send_email

    _patch_mail_configuration(monkeypatch, send_email)

    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    send_email.send_email(
        "Subject",
        "Body",
        recipients="override1@example.com, override2@example.com",
    )

    assert PROJECT_SMTP_CALLS, "SMTP connection should have been created"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert smtp_instance.started_tls is True
    assert smtp_instance.logged_in is True

    assert len(smtp_instance.sent_messages) == 1
    from_addr, to_addrs, message = smtp_instance.sent_messages[0]
    assert from_addr == "from@example.com"
    assert to_addrs == ["override1@example.com", "override2@example.com"]
    assert "To: override1@example.com, override2@example.com" in message


def test_send_email_supports_utf8_headers(monkeypatch):
    from monitoring import send_email

    _patch_mail_configuration(
        monkeypatch,
        send_email,
        from_addr="Monitoring System <monitor@example.com>",
        to_addrs="Alice <alice@example.com>, Bob <bob@example.com>",
    )

    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    subject = "Test Alert"
    body = "The system encountered an error."

    send_email.send_email(subject, body)

    assert PROJECT_SMTP_CALLS, "SMTP connection should have been created"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert smtp_instance.started_tls is True
    assert len(smtp_instance.sent_messages) == 1

    from_addr, to_addrs, message = smtp_instance.sent_messages[0]
    assert from_addr == "monitor@example.com"
    assert to_addrs == ["zhangsan@example.com", "lisi@example.com"]

    parsed = message_from_string(message)
    subject_header = str(make_header(decode_header(parsed["Subject"])))
    assert subject_header == subject

    to_header = parsed.get_all("To")
    parsed_recipients = []
    for name, addr in getaddresses(to_header):
        decoded_name = str(make_header(decode_header(name))) if name else ""
        parsed_recipients.append((decoded_name, addr))
    assert parsed_recipients == [
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
    ]

    from_header = str(make_header(decode_header(parsed["From"])))
    assert from_header == "Monitoring System <monitor@example.com>"

    assert parsed.is_multipart() is True
    payload_part = parsed.get_payload()[0]
    assert payload_part.get_content_charset() == "utf-8"
    assert payload_part.get_payload(decode=True).decode("utf-8") == body


def test_build_outage_messages_localized_in_chinese(monkeypatch):
    from monitoring import send_email

    template_manager = configuration.TemplateManager()
    monkeypatch.setattr(configuration, "get_template_manager",
                        lambda: template_manager)
    monkeypatch.setattr(configuration,
                        "_LANGUAGE_CACHE",
                        "zh_CN",
                        raising=False)

    template_manager.reload()

    service_name = "Sample Service"
    occurred_at = "2024-01-02 03:04:05"

    alert_subject, _ = send_email.build_outage_alert_message(
        service_name, occurred_at)
    recovery_subject, _ = send_email.build_outage_recovery_message(
        service_name, occurred_at)

    assert alert_subject == f"Outage Alert | {service_name}"
    assert recovery_subject == f"Outage Recovery | {service_name}"


def test_send_email_uses_ssl_when_configured(monkeypatch):
    from monitoring import send_email

    _patch_mail_configuration(
        monkeypatch,
        send_email,
        use_starttls=False,
        use_ssl=True,
    )

    monkeypatch.setattr(send_email.smtplib, "SMTP_SSL", DummySMTPSSL)
    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    send_email.send_email("Subject", "Body")

    assert PROJECT_SMTP_CALLS, "SMTP_SSL connection should have been created"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert isinstance(smtp_instance, DummySMTPSSL)
    assert smtp_instance.started_tls is False
    assert smtp_instance.logged_in is True


def test_send_email_supports_plain_connection(monkeypatch):
    from monitoring import send_email

    _patch_mail_configuration(
        monkeypatch,
        send_email,
        use_starttls=False,
        use_ssl=False,
    )

    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    class FailSSL:

        def __init__(self, *args, **kwargs):
            pytest.fail("SMTP_SSL should not be used here")

    monkeypatch.setattr(send_email.smtplib, "SMTP_SSL", FailSSL)

    send_email.send_email("Subject", "Body")

    assert PROJECT_SMTP_CALLS, "Plain SMTP connection should have been created"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert isinstance(smtp_instance, DummySMTP)
    assert smtp_instance.started_tls is False
    assert smtp_instance.logged_in is True


def test_send_email_rejects_conflicting_tls(monkeypatch):
    from monitoring import send_email

    _patch_mail_configuration(
        monkeypatch,
        send_email,
        use_starttls=True,
        use_ssl=True,
    )

    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    with pytest.raises(ValueError, match="use_starttls"):
        send_email.send_email("Subject", "Body")


def test_send_email_logs_authentication_error(monkeypatch, caplog):
    from monitoring import send_email

    _patch_mail_configuration(monkeypatch, send_email)

    class AuthFailSMTP(DummySMTP):

        def login(self, username,
                  password):  # noqa: D401 - keep signature identical to parent
            raise smtplib.SMTPAuthenticationError(535, b"Auth failed")

    monkeypatch.setattr(send_email.smtplib, "SMTP", AuthFailSMTP)

    with caplog.at_level(logging.ERROR, logger="monitoring.send_email"):
        with pytest.raises(smtplib.SMTPAuthenticationError):
            send_email.send_email("Subject", "Body")

    assert "SMTP authentication failed" in caplog.text
    assert "mail.smtp.authentication_error" in caplog.text


def test_send_email_logs_smtp_exception(monkeypatch, caplog):
    from monitoring import send_email

    _patch_mail_configuration(monkeypatch, send_email)

    class SendFailSMTP(DummySMTP):

        def sendmail(self, from_addr, to_addrs, message):  # noqa: D401
            raise smtplib.SMTPException("send failed")

    monkeypatch.setattr(send_email.smtplib, "SMTP", SendFailSMTP)

    with caplog.at_level(logging.ERROR, logger="monitoring.send_email"):
        with pytest.raises(smtplib.SMTPException):
            send_email.send_email("Subject", "Body")

    assert "SMTP communication error" in caplog.text
    assert "mail.smtp.communication_error" in caplog.text


def test_read_mail_configuration_bootstraps_placeholder(tmp_path, monkeypatch):
    monkeypatch.setenv(configuration.LOG_DIR_ENV, str(tmp_path))

    config_dir = tmp_path / "Config"
    config_file = config_dir / "Config.ini"

    assert not config_file.exists()

    with pytest.raises(ValueError) as excinfo:
        configuration.read_mail_configuration()

    message = str(excinfo.value)
    assert "real SMTP settings" in message
    assert "README" in message

    assert config_dir.is_dir()
    assert config_file.is_file()


def test_read_mail_configuration_rejects_invalid_boolean_env(monkeypatch):
    env_values = {
        configuration.MAIL_ENV_MAP["smtp_server"]: "smtp.example.com",
        configuration.MAIL_ENV_MAP["smtp_port"]: "465",
        configuration.MAIL_ENV_MAP["username"]: "user",
        configuration.MAIL_ENV_MAP["password"]: "secret",
        configuration.MAIL_ENV_MAP["from_addr"]: "from@example.com",
        configuration.MAIL_ENV_MAP["to_addrs"]: "to@example.com",
        configuration.MAIL_ENV_MAP["use_starttls"]: "maybe",
        configuration.MAIL_ENV_MAP["use_ssl"]: "false",
    }

    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(ValueError, match="use_starttls"):
        configuration.read_mail_configuration()


def test_send_email_supports_minimal_env_configuration(monkeypatch):
    required_values = {
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "username": "user",
        "password": "secret",
        "from_addr": "from@example.com",
        "to_addrs": "to@example.com",
    }

    for key, env_name in configuration.MAIL_ENV_MAP.items():
        monkeypatch.delenv(env_name, raising=False)
        if key in required_values:
            monkeypatch.setenv(env_name, required_values[key])

    monkeypatch.delenv(configuration.EXTERNAL_MAIL_CONFIG_ENV, raising=False)

    mail_config = configuration.read_mail_configuration()

    for key, expected in required_values.items():
        assert mail_config[key] == expected

    for key in configuration.OPTIONAL_MAIL_BOOL_KEYS:
        assert mail_config[key] is False

    from monitoring import send_email

    monkeypatch.setattr(send_email.smtplib, "SMTP", DummySMTP)

    class FailSSL:

        def __init__(self, *args,
                     **kwargs):  # noqa: D401 - align with SMTP_SSL interface
            pytest.fail("SMTP_SSL should not be used here")

    monkeypatch.setattr(send_email.smtplib, "SMTP_SSL", FailSSL)

    send_email.send_email("Subject", "Body")

    assert PROJECT_SMTP_CALLS, "SMTP connection should have been created"
    smtp_instance = PROJECT_SMTP_CALLS[0]
    assert isinstance(smtp_instance, DummySMTP)
    assert smtp_instance.started_tls is False
    assert smtp_instance.logged_in is True
