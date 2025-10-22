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


@pytest.fixture(autouse=True)
def reset_smtp_calls():
    PROJECT_SMTP_CALLS.clear()
    yield
    PROJECT_SMTP_CALLS.clear()


def test_send_email_prefers_explicit_recipients(monkeypatch):
    import sendEmail

    monkeypatch.setattr(sendEmail.configuration, "read_mail_configuration", lambda: {
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "username": "user",
        "password": "secret",
        "from_addr": "from@example.com",
        "to_addrs": "default@example.com",
    })

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
