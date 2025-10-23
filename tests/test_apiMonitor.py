import logging
import socket
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

from monitoring import api_monitor  # noqa: E402  pylint: disable=wrong-import-position
from monitoring import http_probe  # noqa: E402  pylint: disable=wrong-import-position
from monitoring import network_probe  # noqa: E402  pylint: disable=wrong-import-position
import configuration  # noqa: E402  pylint: disable=wrong-import-position


ORIGINAL_GET_REQUEST_TIMEOUT = configuration.get_request_timeout


class DummyResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.fixture(autouse=True)
def stub_request_timeout(monkeypatch):
    monkeypatch.setattr(configuration, "get_request_timeout", lambda: 5.0)


@pytest.mark.parametrize("status_code", [200, 204, 301, 302])
def test_monitor_get_success_for_valid_status(monkeypatch, caplog, status_code):
    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(status_code)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_get("http://example.com") is True
    assert "monitor.http.success" in caplog.text


def test_monitor_get_failure_status(monkeypatch, caplog):
    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(404)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_get("http://example.com") is False
    assert "monitor.http.failure" in caplog.text
    assert "status=404" in caplog.text


def test_monitor_get_exception(monkeypatch, caplog):
    def fake_get(url, timeout):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_get("http://example.com") is False
    assert "monitor.http.error" in caplog.text
    assert "request timed out" in caplog.text


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
    monkeypatch.setattr(http_probe, "resolve_timeout", fake_resolve_timeout)
    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    assert api_monitor.monitor_get("http://example.com") is False
    assert calls["count"] == 1


def test_monitor_get_uses_explicit_timeout(monkeypatch):
    def fail_if_called():
        raise AssertionError("configuration timeout should not be used")

    def fake_get(url, timeout):
        assert timeout == 1.5
        return DummyResponse(200)

    monkeypatch.setattr(configuration, "get_request_timeout", fail_if_called)
    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    assert api_monitor.monitor_get("http://example.com", timeout=1.5) is True


def test_monitor_get_handles_timeout_configuration_error(monkeypatch, caplog):
    def fake_get_timeout():
        raise ValueError("invalid timeout")

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_get("http://example.com") is False
    assert "monitor.http.timeout_error" in caplog.text
    assert "invalid timeout" in caplog.text


@pytest.mark.parametrize("status_code", [200, 204, 302])
def test_monitor_post_success_for_valid_status(monkeypatch, caplog, status_code):
    def fake_post(url, data=None, headers=None, timeout=None):
        assert data == {}
        assert headers is None
        assert timeout == 5.0
        return DummyResponse(status_code)

    monkeypatch.setattr(http_probe.requests, "post", fake_post)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_post("http://example.com", payload={}) is True
    assert "monitor.http.success" in caplog.text


def test_monitor_post_failure_status(monkeypatch, caplog):
    def fake_post(url, data=None, headers=None, timeout=None):
        assert data == {}
        assert headers is None
        assert timeout == 5.0
        return DummyResponse(500)

    monkeypatch.setattr(http_probe.requests, "post", fake_post)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_post("http://example.com", payload={}) is False
    assert "monitor.http.failure" in caplog.text
    assert "status=500" in caplog.text


def test_monitor_post_exception(monkeypatch, caplog):
    def fake_post(url, data=None, headers=None, timeout=None):
        raise requests.ConnectionError("connection aborted")

    monkeypatch.setattr(http_probe.requests, "post", fake_post)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_post("http://example.com", payload={}) is False
    assert "monitor.http.error" in caplog.text
    assert "connection aborted" in caplog.text


def test_monitor_post_handles_timeout_configuration_error(monkeypatch, caplog):
    def fake_get_timeout():
        raise ValueError("invalid timeout")

    def fail_post(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("requests.post should not be invoked")

    monkeypatch.setattr(configuration, "get_request_timeout", fake_get_timeout)
    monkeypatch.setattr(http_probe.requests, "post", fail_post)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert api_monitor.monitor_post("http://example.com", payload={}) is False
    assert "monitor.http.timeout_error" in caplog.text
    assert "invalid timeout" in caplog.text


def test_monitor_post_forwards_payload_and_headers(monkeypatch):
    observed = {}

    def fake_post(url, data=None, headers=None, timeout=None):
        observed["url"] = url
        observed["data"] = data
        observed["headers"] = headers
        observed["timeout"] = timeout
        return DummyResponse(200)

    monkeypatch.setattr(http_probe.requests, "post", fake_post)

    payload = {"key": "value"}
    headers = {"X-Test": "1"}

    assert (
        api_monitor.monitor_post(
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


def test_monitor_requests_refresh_timeout_after_configuration_reload(
    monkeypatch, tmp_path
):
    monkeypatch.delenv(configuration.REQUEST_TIMEOUT_ENV, raising=False)

    config_root = tmp_path / configuration.APPLICATION_HOME_NAME
    config_dir = config_root / "Config"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "Config.ini"
    config_file.write_text("[Request]\ntimeout = 2.5\n", encoding="utf-8")

    monkeypatch.setattr(configuration, "get_logdir", lambda: str(config_root) + "/")
    monkeypatch.setattr(configuration, "get_request_timeout", ORIGINAL_GET_REQUEST_TIMEOUT)
    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()

    configuration.reset_request_timeout_cache()

    observed_get = []
    observed_post = []

    def fake_get(url, timeout):
        observed_get.append(timeout)
        return DummyResponse(200)

    def fake_post(url, data=None, headers=None, timeout=None):
        observed_post.append(timeout)
        return DummyResponse(200)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)
    monkeypatch.setattr(http_probe.requests, "post", fake_post)

    assert api_monitor.monitor_get("http://example.com/status") is True
    assert observed_get == [2.5]

    config_file.write_text("[Request]\ntimeout = 9.0\n", encoding="utf-8")
    configuration.reset_request_timeout_cache()

    assert api_monitor.monitor_get("http://example.com/status") is True
    assert observed_get == [2.5, 9.0]

    assert api_monitor.monitor_post("http://example.com/api", payload={}) is True
    assert observed_post == [9.0]

    ORIGINAL_GET_REQUEST_TIMEOUT.cache_clear()


def test_monitor_server_handles_socket_gaierror(monkeypatch, caplog):
    def fake_create_connection(*args, **kwargs):
        raise socket.gaierror("name or service not known")

    monkeypatch.setattr(network_probe.socket, "create_connection", fake_create_connection)

    ping_calls = {"subprocess": 0}

    def fake_subprocess_ping(host, timeout):
        ping_calls["subprocess"] += 1
        assert timeout == 5.0
        return False

    monkeypatch.setattr(network_probe, "_subprocess_ping", fake_subprocess_ping)

    class DummyPing:
        def request_ping(self, *args, **kwargs):
            return b"icmp"

        def raw_socket(self, *args, **kwargs):
            raise PermissionError("raw sockets not permitted")

        def reply_ping(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(network_probe, "IcmpProbe", DummyPing)

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

    monkeypatch.setattr(network_probe.socket, "socket", fake_socket_factory)

    def fake_get(url, timeout):
        assert url == "http://invalid.host"
        assert timeout == 5.0
        return DummyResponse(503)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        result = api_monitor.monitor_server(("http", "invalid.host", None, None))

    assert result is False

    assert "monitor.socket.offline" in caplog.text
    assert "status=503" in caplog.text
    assert "monitor.server.summary" in caplog.text
    assert ping_calls["subprocess"] == 1


def test_monitor_server_requires_http_success(monkeypatch, caplog):
    monkeypatch.setattr(
        network_probe,
        "check_socket_connectivity",
        lambda host, port, timeout: True,
    )
    monkeypatch.setattr(
        network_probe,
        "perform_ping_probe",
        lambda host, timeout: True,
    )
    monkeypatch.setattr(
        network_probe,
        "perform_icmp_probe",
        lambda host, timeout: None,
    )

    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(502)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        result = api_monitor.monitor_server(("http", "reachable.example", 8080, None))

    assert result is False

    assert "monitor.server.summary" in caplog.text
    assert "socket=True" in caplog.text
    assert "ping=True" in caplog.text
    assert "monitor.server.network_only" in caplog.text


def test_perform_ping_probe_distributes_timeout(monkeypatch):
    configured_timeout = 0.6
    sleep_calls = []

    class DummySocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    reply_results = [0.05, -1, -1]

    class DummyPing:
        def __init__(self):
            self.reply_timeouts = []
            self.sequences = []

        def request_ping(self, *args, **kwargs):
            return b"icmp"

        def raw_socket(self, dst_addr, icmp_packet):
            return 0.0, DummySocket()

        def reply_ping(self, send_request_ping_time, rawsocket, sequence, timeout=None):
            self.reply_timeouts.append(timeout)
            self.sequences.append(sequence)
            return reply_results.pop(0)

    dummy_ping = DummyPing()

    monkeypatch.setattr(network_probe, "IcmpProbe", lambda: dummy_ping)
    monkeypatch.setattr(network_probe.socket, "gethostbyname", lambda host: "127.0.0.1")

    def fake_sleep(duration):
        sleep_calls.append(duration)

    monkeypatch.setattr(network_probe.time, "sleep", fake_sleep)

    result = network_probe.perform_ping_probe("example.com", configured_timeout)

    assert result is True
    per_attempt_timeout = configured_timeout / 3
    assert dummy_ping.reply_timeouts[0] == pytest.approx(per_attempt_timeout)
    assert dummy_ping.reply_timeouts[1] == pytest.approx(per_attempt_timeout)
    assert dummy_ping.reply_timeouts[2] == pytest.approx(0.0)
    assert dummy_ping.sequences == [1, 2, 3]
    assert sleep_calls == [pytest.approx(min(per_attempt_timeout, 0.7))]
    assert reply_results == []


@pytest.fixture
def stub_monitor_server_dependencies(monkeypatch):
    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        network_probe.socket,
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

    monkeypatch.setattr(network_probe, "IcmpProbe", DummyPing)
    monkeypatch.setattr(network_probe, "_subprocess_ping", lambda host, timeout: False)

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
        network_probe.socket,
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

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    assert (
        api_monitor.monitor_server(("https", "example.com", None, "status"))
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

    config_root = tmp_path / configuration.APPLICATION_HOME_NAME
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

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    assert (
        api_monitor.monitor_server(("http", "example.org", None, None))
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
        network_probe.socket,
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

    monkeypatch.setattr(network_probe, "IcmpProbe", CountingPing)
    monkeypatch.setattr(network_probe, "_subprocess_ping", lambda host, timeout: False)
    monkeypatch.setattr(network_probe.socket, "gethostbyname", lambda host: "127.0.0.1")

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

    monkeypatch.setattr(network_probe.socket, "socket", lambda *args, **kwargs: DummyIcmpSocket())
    monkeypatch.setattr(network_probe.time, "sleep", lambda *_args, **_kwargs: None)

    def fake_get(url, timeout):
        assert timeout == 5.0
        return DummyResponse(200)

    monkeypatch.setattr(http_probe.requests, "get", fake_get)

    result = api_monitor.monitor_server(("http", "example.org", None, None))

    assert result is True
    assert close_counts["count"] == 3
