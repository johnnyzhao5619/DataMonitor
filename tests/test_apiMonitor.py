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

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)
    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert apiMonitor.monitor_get("http://example.com") is False
    assert calls["count"] == 1


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


def test_monitor_post_reads_configuration_timeout(monkeypatch):
    calls = {"count": 0}

    def fake_get_timeout():
        calls["count"] += 1
        return 2.5

    def fake_post(url, data, timeout):
        assert timeout == 2.5
        raise requests.RequestException("boom")

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)
    monkeypatch.setattr(apiMonitor.requests, "post", fake_post)

    assert apiMonitor.monitor_post("http://example.com", payload={}) is False
    assert calls["count"] == 1
