import socket
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


def test_monitor_get_reads_configuration_timeout(monkeypatch):
    calls = {"count": 0}

    def fake_get_timeout():
        calls["count"] += 1
        return 3.5

    def fake_get(url, timeout):
        assert timeout == 3.5
        raise requests.RequestException("boom")

    cached_timeout = {"value": None}

    def fake_resolve_timeout(explicit_timeout=None):
        if explicit_timeout is not None:
            return explicit_timeout
        if cached_timeout["value"] is None:
            cached_timeout["value"] = configuration.get_request_timeout()
        return cached_timeout["value"]

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)
    monkeypatch.setattr(apiMonitor, "_resolve_timeout", fake_resolve_timeout)
    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com") is False
    assert calls["count"] == 1


def test_monitor_get_uses_explicit_timeout(monkeypatch):
    def fail_if_called():
        raise AssertionError("configuration timeout should not be used")

    def fake_get(url, timeout):
        assert timeout == 1.5
        return DummyResponse(200)

    monkeypatch.setattr(configuration, "get_request_timeout", fail_if_called)
    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com", timeout=1.5) is True


def test_monitor_get_handles_timeout_configuration_error(monkeypatch, capsys):
    def fake_get_timeout():
        raise ValueError("invalid timeout")

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)

    assert apiMonitor.monitor_get("http://example.com") is False

    captured = capsys.readouterr()
    assert "invalid timeout" in captured.out


@pytest.mark.parametrize("status_code", [200, 204, 302])
def test_monitor_post_success_for_valid_status(monkeypatch, status_code):
    def fake_post(url, data=None, headers=None, timeout=None):
        assert data == {}
        assert headers is None
        assert timeout == 5.0
        return DummyResponse(status_code)

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is True


def test_monitor_post_failure_status(monkeypatch, capsys):
    def fake_post(url, data=None, headers=None, timeout=None):
        assert data == {}
        assert headers is None
        assert timeout == 5.0
        return DummyResponse(500)

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is False

    captured = capsys.readouterr()
    assert "500" in captured.out


def test_monitor_post_exception(monkeypatch, capsys):
    def fake_post(url, data=None, headers=None, timeout=None):
        raise requests.ConnectionError("connection aborted")

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is False

    captured = capsys.readouterr()
    assert "connection aborted" in captured.out


def test_monitor_post_forwards_payload_and_headers(monkeypatch):
    observed = {}

    def fake_post(url, data=None, headers=None, timeout=None):
        observed["url"] = url
        observed["data"] = data
        observed["headers"] = headers
        observed["timeout"] = timeout
        return DummyResponse(200)

    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    payload = {"key": "value"}
    headers = {"X-Test": "1"}

    assert (
        apiMonitor.monitor_post(
            "http://example.com/api",
            payload=payload,
            headers=headers,
        )
        is True
    )

    assert observed == {
        "url": "http://example.com/api",
        "data": payload,
        "headers": headers,
        "timeout": 5.0,
    }


def test_monitor_server_handles_socket_gaierror(monkeypatch, capsys):
    def fake_create_connection(*args, **kwargs):
        raise socket.gaierror("name or service not known")

    monkeypatch.setattr(apiMonitor.socket, "create_connection", fake_create_connection)

    ping_calls = {"subprocess": 0}

    def fake_subprocess_ping(host):
        ping_calls["subprocess"] += 1
        return False

    monkeypatch.setattr(apiMonitor, "_subprocess_ping", fake_subprocess_ping)

    class DummyPing:
        def request_ping(self, *args, **kwargs):
            return b"icmp"

        def raw_socket(self, *args, **kwargs):
            raise PermissionError("raw sockets not permitted")

        def reply_ping(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(apiMonitor, "MyPing", DummyPing)

    def fake_socket_factory(*args, **kwargs):
        class DummySocket:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def sendto(self, *args, **kwargs):
                return None

            def settimeout(self, *args, **kwargs):
                return None

            def recv(self, *args, **kwargs):
                raise socket.timeout("no icmp reply")

        return DummySocket()

    monkeypatch.setattr(apiMonitor.socket, "socket", fake_socket_factory)

    def fake_get(url, timeout):
        assert url == "http://invalid.host"
        return DummyResponse(503)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    result = apiMonitor.monitor_server(("http", "invalid.host", None, None))

    assert result is False

    captured = capsys.readouterr()
    assert "offline (Socket)" in captured.out
    assert "503" in captured.out
    assert ping_calls["subprocess"] == 1
