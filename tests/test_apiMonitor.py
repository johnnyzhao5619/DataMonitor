import textwrap
import types
import sys
from pathlib import Path

import pytest


class _RequestException(Exception):
    pass


class _Timeout(_RequestException):
    pass


class _ConnectionError(_RequestException):
    pass


requests_stub = types.ModuleType("requests")
requests_stub.RequestException = _RequestException
requests_stub.Timeout = _Timeout
requests_stub.ConnectionError = _ConnectionError
requests_stub.get = None
requests_stub.post = None

sys.modules.setdefault("requests", requests_stub)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests  # noqa: E402  pylint: disable=wrong-import-position

import apiMonitor  # noqa: E402  pylint: disable=wrong-import-position
import configuration  # noqa: E402  pylint: disable=wrong-import-position


class DummyResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.fixture(autouse=True)
def stub_request_timeout(monkeypatch):
    monkeypatch.setattr(configuration, "get_request_timeout", lambda: 5.0)


@pytest.fixture(autouse=True)
def stub_resolve_timeout(monkeypatch):
    monkeypatch.setattr(apiMonitor, "_resolve_timeout", lambda timeout=None: 5.0, raising=False)
    monkeypatch.setattr(apiMonitor, "resolved_timeout", 5.0, raising=False)


@pytest.mark.parametrize("status_code", [200, 204, 301, 302])
def test_monitor_get_success_for_valid_status(monkeypatch, status_code):
    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(status_code)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com") is True


def test_monitor_get_failure_status(monkeypatch, capsys):
    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(404)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com") is False

    captured = capsys.readouterr()
    assert "404" in captured.out


def test_monitor_get_exception(monkeypatch, capsys):
    def fake_get(url, timeout):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com") is False

    captured = capsys.readouterr()
    assert "request timed out" in captured.out


@pytest.mark.parametrize("status_code", [200, 204, 302])
def test_monitor_post_success_for_valid_status(monkeypatch, status_code):
    def fake_post(url, data, timeout):
        assert timeout == 5.0
        return DummyResponse(status_code)

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is True


def test_monitor_post_failure_status(monkeypatch, capsys):
    def fake_post(url, data, timeout):
        assert timeout == 5.0
        return DummyResponse(500)

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is False

    captured = capsys.readouterr()
    assert "500" in captured.out


def test_monitor_post_exception(monkeypatch, capsys):
    def fake_post(url, data, timeout):
        raise requests.ConnectionError("connection aborted")

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is False

    captured = capsys.readouterr()
    assert "connection aborted" in captured.out


def _write_config(tmp_path, content: str):
    config_dir = tmp_path / "APIMonitor" / "Config"
    config_dir.mkdir(parents=True)
    (config_dir / "Config.ini").write_text(textwrap.dedent(content), encoding="utf-8")


def test_read_monitor_list_with_optional_fields(monkeypatch, tmp_path):
    _write_config(
        tmp_path,
        """
        [MonitorNum]
        total = 1

        [Monitor1]
        name = ServiceA
        url = https://service.example.com
        type = API
        interval = 30
        email = ops@example.com
        payload = {"token": "abc123"}
        headers = Accept=application/json, X-Trace=42
        """,
    )

    monkeypatch.setattr(
        configuration, "get_logdir", lambda: str(tmp_path / "APIMonitor") + "/"
    )

    monitor_list = configuration.read_monitor_list()

    assert len(monitor_list) == 1
    monitor = monitor_list[0]
    assert monitor["payload"] == {"token": "abc123"}
    assert monitor["headers"] == {"Accept": "application/json", "X-Trace": "42"}


def test_read_monitor_list_skip_invalid_optional(monkeypatch, tmp_path, caplog):
    _write_config(
        tmp_path,
        """
        [MonitorNum]
        total = 2

        [Monitor1]
        name = ServiceA
        url = https://service.example.com
        type = API
        interval = 30
        email = ops@example.com
        payload = key1=value1

        [Monitor2]
        name = ServiceB
        url = https://invalid.example.com
        type = API
        interval = 45
        email = ops@example.com
        payload = invalid
        """,
    )

    monkeypatch.setattr(
        configuration, "get_logdir", lambda: str(tmp_path / "APIMonitor") + "/"
    )
    caplog.clear()

    monitor_list = configuration.read_monitor_list()

    assert len(monitor_list) == 1
    assert monitor_list[0]["name"] == "ServiceA"
    assert any("Monitor2" in record.message for record in caplog.records)
