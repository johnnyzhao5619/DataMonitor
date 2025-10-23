# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : apiMonitor.py
# @Software: PyCharm
import logging
import math
import os
import shutil
import socket
import subprocess
import time
from contextlib import closing

import requests

import configuration
from myPing import MyPing


LOGGER = logging.getLogger(__name__)

def _resolve_timeout(explicit_timeout=None):
    if explicit_timeout is not None:
        return explicit_timeout
    return configuration.get_request_timeout()

def _subprocess_ping(host, timeout):
    """Fallback ping using system command. Returns True on success."""
    timeout = max(float(timeout), 0.0)
    if os.name == 'nt':
        wait_ms = max(int(math.ceil(timeout * 1000)), 1)
        ping_cmd = ['ping', '-n', '1', '-w', str(wait_ms), host]
    else:
        wait_seconds = max(int(math.ceil(timeout)), 1)
        ping_cmd = ['ping', '-c', '1', '-W', str(wait_seconds), host]

    if shutil.which(ping_cmd[0]) is None:
        LOGGER.warning(
            "monitor.ping.subprocess.command_missing command=%s", ping_cmd[0]
        )
        return False

    try:
        subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT)
        LOGGER.info("monitor.ping.subprocess.success host=%s", host)
        return True
    except subprocess.CalledProcessError as exc:
        LOGGER.warning("monitor.ping.subprocess.failure host=%s error=%s", host, exc)
        return False

def _perform_http_request(
    method_name,
    request_callable,
    url,
    *,
    timeout,
    payload=None,
    headers=None,
):
    request_kwargs = {"timeout": timeout}
    if payload is not None:
        request_kwargs["data"] = payload
    if headers is not None:
        request_kwargs["headers"] = headers

    try:
        response = request_callable(url, **request_kwargs)
    except requests.RequestException as exc:
        LOGGER.error(
            "monitor.http.error method=%s url=%s error=%s", method_name, url, exc
        )
        return False

    if 200 <= response.status_code < 400:
        LOGGER.info(
            "monitor.http.success method=%s url=%s status=%s",
            method_name,
            url,
            response.status_code,
        )
        return True

    LOGGER.warning(
        "monitor.http.failure method=%s url=%s status=%s",
        method_name,
        url,
        response.status_code,
    )
    return False

def monitor_get(url, timeout=None):
    try:
        resolved_timeout = _resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error("monitor.http.timeout_error method=GET url=%s error=%s", url, exc)
        return False

    return _perform_http_request(
        "GET",
        requests.get,
        url,
        timeout=resolved_timeout,
    )

def monitor_post(url, payload=None, *, headers=None, timeout=None):
    try:
        resolved_timeout = _resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error(
            "monitor.http.timeout_error method=POST url=%s error=%s", url, exc
        )
        return False
    return _perform_http_request(
        "POST",
        requests.post,
        url,
        timeout=resolved_timeout,
        payload=payload,
        headers=headers,
    )

def _compose_service_url(protocol, host, port, suffix, explicit_port):
    base_url = f"{protocol}://{host}"
    if explicit_port:
        base_url = f"{base_url}:{port}"
    if suffix:
        base_url = f"{base_url}/{suffix}"
    return base_url

def _check_socket_connectivity(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        LOGGER.info("monitor.socket.success host=%s port=%s", host, port)
        return True
    except OSError as exc:
        LOGGER.warning(
            "monitor.socket.offline host=%s port=%s error=%s", host, port, exc
        )
        return False

def _perform_ping_probe(host, timeout):
    try:
        ping = MyPing()
        status = []
        data_type = 8
        data_code = 0
        data_checksum = 0
        data_id = 0
        data_sequence = 1
        payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'
        dst_addr = socket.gethostbyname(host)
        LOGGER.info(
            "monitor.ping.raw.start host=%s destination=%s payload_size=%s",
            host,
            dst_addr,
            len(payload_body),
        )
        for i in range(3):
            icmp_packet = ping.request_ping(
                data_type,
                data_code,
                data_checksum,
                data_id,
                data_sequence + i,
                payload_body,
            )
            send_request_ping_time, rawsocket_resource = ping.raw_socket(dst_addr, icmp_packet)
            if not hasattr(rawsocket_resource, "__enter__") or not hasattr(rawsocket_resource, "__exit__"):
                rawsocket_resource = closing(rawsocket_resource)

            with rawsocket_resource as rawsocket:
                times = ping.reply_ping(send_request_ping_time, rawsocket, data_sequence + i)
            if times > 0:
                LOGGER.info(
                    "monitor.ping.raw.reply host=%s destination=%s sequence=%s rtt_ms=%s",
                    host,
                    dst_addr,
                    data_sequence + i,
                    int(times * 1000),
                )
                status.append(True)
                time.sleep(0.7)
            else:
                status.append(False)
                LOGGER.warning(
                    "monitor.ping.raw.timeout host=%s destination=%s sequence=%s",
                    host,
                    dst_addr,
                    data_sequence + i,
                )

        success = any(status)
        if success:
            LOGGER.info("monitor.ping.raw.success host=%s", host)
        else:
            LOGGER.warning("monitor.ping.raw.failure host=%s", host)
        return success
    except (PermissionError, OSError) as exc:
        LOGGER.warning(
            "monitor.ping.raw.permission_denied host=%s error=%s", host, exc
        )
        return _subprocess_ping(host, timeout)
    except Exception as exc:
        LOGGER.warning(
            "monitor.ping.raw.error host=%s error=%s", host, exc
        )
        return _subprocess_ping(host, timeout)

def _perform_icmp_probe(host, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            dummy_packet = b'\x08\x00\x7d\x4b\x00\x00\x00\x00PingData'
            sock.sendto(dummy_packet, (host, 0))
            sock.settimeout(timeout)
            sock.recv(1024)
            LOGGER.info("monitor.icmp.success host=%s", host)
            return True
    except PermissionError as exc:
        LOGGER.warning(
            "monitor.icmp.permission_denied host=%s error=%s", host, exc
        )
    except (socket.timeout, socket.error) as exc:
        LOGGER.warning("monitor.icmp.failure host=%s error=%s", host, exc)
    return False

def _perform_http_probe(url, timeout):
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        LOGGER.error("monitor.http_probe.error url=%s error=%s", url, exc)
        return False

    status_code = response.status_code
    if 200 <= status_code < 400:
        LOGGER.info(
            "monitor.http_probe.success url=%s status=%s", url, status_code
        )
        return True

    LOGGER.warning(
        "monitor.http_probe.failure url=%s status=%s", url, status_code
    )
    return False

def monitor_server(address, timeout=None):
    protocol, host, port, suffix = address
    if protocol not in ('http', 'https'):
        protocol = 'http'

    default_port = 80 if protocol == 'http' else 443
    explicit_port = port is not None
    port = port if explicit_port else default_port

    try:
        resolved_timeout = _resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error("monitor.server.timeout_error host=%s error=%s", host, exc)
        return False

    url = _compose_service_url(protocol, host, port, suffix, explicit_port)

    LOGGER.info("monitor.server.start host=%s port=%s url=%s", host, port, url)

    socket_success = _check_socket_connectivity(host, port, resolved_timeout)
    ping_success = _perform_ping_probe(host, resolved_timeout)
    _perform_icmp_probe(host, resolved_timeout)

    http_success = _perform_http_probe(url, resolved_timeout)

    LOGGER.info(
        "monitor.server.summary host=%s socket=%s ping=%s http=%s",
        host,
        socket_success,
        ping_success,
        http_success,
    )

    if http_success:
        return True

    if socket_success or ping_success:
        LOGGER.warning("monitor.server.network_only host=%s", host)

    else:
        LOGGER.error("monitor.server.offline host=%s", host)

    return False
