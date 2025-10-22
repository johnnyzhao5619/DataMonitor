import socket
import importlib
import textwrap
import types
import sys
from contextlib import closing
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


ORIGINAL_GET_REQUEST_TIMEOUT = configuration.get_request_timeout


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

    def fake_subprocess_ping(host, timeout):
        ping_calls["subprocess"] += 1
        assert timeout == 5.0
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

            def settimeout(self, timeout):
                assert timeout == 5.0
                return None

            def recv(self, *args, **kwargs):
                raise socket.timeout("no icmp reply")

        return DummySocket()

    monkeypatch.setattr(apiMonitor.socket, "socket", fake_socket_factory)

    def fake_get(url, timeout):
        assert url == "http://invalid.host"
        assert timeout == 5.0
        return DummyResponse(503)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    result = apiMonitor.monitor_server(("http", "invalid.host", None, None))

    assert result is False

    captured = capsys.readouterr()
    assert "offline (Socket)" in captured.out
    assert "503" in captured.out
    assert "探测结果: socket=False, ping=False, http=False" in captured.out
    assert ping_calls["subprocess"] == 1


@pytest.fixture
def stub_monitor_server_dependencies(monkeypatch):
    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        apiMonitor.socket,
        "create_connection",
        lambda *args, **kwargs: DummyConnection(),
    )

    class DummyPing:
        def request_ping(self, *args, **kwargs):
            return b"icmp"

        def raw_socket(self, *args, **kwargs):
            raise PermissionError("raw sockets not permitted")

        def reply_ping(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(apiMonitor, "MyPing", DummyPing)
    monkeypatch.setattr(apiMonitor, "_subprocess_ping", lambda host, timeout: False)

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

    monkeypatch.setattr(
        apiMonitor.socket,
        "socket",
        lambda *args, **kwargs: DummySocket(),
    )


def test_monitor_server_uses_timeout_from_environment(
    monkeypatch, stub_monitor_server_dependencies
):
    monkeypatch.setenv(configuration.REQUEST_TIMEOUT_ENV, "12.5")
    monkeypatch.setattr(configuration, "get_request_timeout", ORIGINAL_GET_REQUEST_TIMEOUT)
    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()

    observed = {}

    def fake_get(url, timeout):
        observed["url"] = url
        observed["timeout"] = timeout
        return DummyResponse(200)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert (
        apiMonitor.monitor_server(("https", "example.com", None, "status"))
        is True
    )
    assert observed == {
        "url": "https://example.com/status",
        "timeout": 12.5,
    }

    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()


def test_monitor_server_uses_timeout_from_config_file(
    monkeypatch, tmp_path, stub_monitor_server_dependencies
):
    monkeypatch.delenv(configuration.REQUEST_TIMEOUT_ENV, raising=False)

    config_root = tmp_path / "APIMonitor"
    (config_root / "Config").mkdir(parents=True)
    config_file = config_root / "Config" / "Config.ini"
    config_file.write_text("[Request]\ntimeout = 3.25\n", encoding="utf-8")

    monkeypatch.setattr(configuration, "get_logdir", lambda: str(config_root) + "/")
    monkeypatch.setattr(configuration, "get_request_timeout", ORIGINAL_GET_REQUEST_TIMEOUT)
    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()

    observed = {}

    def fake_get(url, timeout):
        observed["url"] = url
        observed["timeout"] = timeout
        return DummyResponse(200)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    assert (
        apiMonitor.monitor_server(("http", "example.org", None, None))
        is True
    )
    assert observed == {
        "url": "http://example.org",
        "timeout": 3.25,
    }

    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()


def test_monitor_server_closes_raw_ping_socket(monkeypatch):
    close_counts = {"count": 0}

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        apiMonitor.socket,
        "create_connection",
        lambda *args, **kwargs: DummyConnection(),
    )

    class CountingSocket:
        def __init__(self):
            self._closed = False

        def close(self):
            if not self._closed:
                self._closed = True
                close_counts["count"] += 1

    class CountingPing:
        def request_ping(self, *args, **kwargs):
            return b"icmp"

        def raw_socket(self, *args, **kwargs):
            return 0.0, closing(CountingSocket())

        def reply_ping(self, *args, **kwargs):
            return 0.01

    monkeypatch.setattr(apiMonitor, "MyPing", CountingPing)
    monkeypatch.setattr(apiMonitor, "_subprocess_ping", lambda host: False)
    monkeypatch.setattr(apiMonitor.socket, "gethostbyname", lambda host: "127.0.0.1")

    class DummyIcmpSocket:
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

    monkeypatch.setattr(apiMonitor.socket, "socket", lambda *args, **kwargs: DummyIcmpSocket())
    monkeypatch.setattr(apiMonitor.time, "sleep", lambda *_args, **_kwargs: None)

    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(200)

    monkeypatch.setattr(apiMonitor.requests, "get", fake_get)

    result = apiMonitor.monitor_server(("http", "example.org", None, None))

    assert result is True
    assert close_counts["count"] == 3


def test_perform_task_unknown_type_logs_and_returns_false(monkeypatch):
    pyqt5_module = types.ModuleType("PyQt5")
    qtwidgets_module = types.ModuleType("PyQt5.QtWidgets")

    class DummyMainWindow:
        def setupUi(self, *_args, **_kwargs):
            return None

    class DummyInputDialog:
        pass

    qtwidgets_module.QMainWindow = type("QMainWindow", (), {})
    qtwidgets_module.QInputDialog = DummyInputDialog
    pyqt5_module.QtWidgets = qtwidgets_module

    monkeypatch.setitem(sys.modules, "PyQt5", pyqt5_module)
    monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", qtwidgets_module)

    gui_stub = types.ModuleType("GUI_Windows_New")
    gui_stub.MainWindow = DummyMainWindow
    monkeypatch.setitem(sys.modules, "GUI_Windows_New", gui_stub)

    monkeypatch.delitem(sys.modules, "mainFrame", raising=False)
    mainFrame = importlib.import_module("mainFrame")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("monitoring function should not be invoked for unsupported type")

    monkeypatch.setattr(mainFrame.apiMonitor, "monitor_get", fail_if_called)
    monkeypatch.setattr(mainFrame.apiMonitor, "monitor_post", fail_if_called)
    monkeypatch.setattr(mainFrame.apiMonitor, "monitor_server", fail_if_called)

    observed = {}

    def fake_record(action, log):
        observed["action"] = action
        observed["log"] = log

    monkeypatch.setattr(mainFrame.logRecorder, "record", fake_record)

    window = mainFrame.toolsetWindow.__new__(mainFrame.toolsetWindow)

    result = window.perform_task("http://example.com", None, "UNKNOWN", "user@example.com")

    assert result is False
    assert observed["action"] == "Unsupported Monitor Type"
    assert "UNKNOWN" in observed["log"]
    assert "http://example.com" in observed["log"]

    sys.modules.pop("mainFrame", None)
