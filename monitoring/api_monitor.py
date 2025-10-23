# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : api_monitor.py
# @Software: PyCharm

import logging

import configuration

from . import http_probe
from . import network_probe


LOGGER = logging.getLogger(__name__)


def _compose_service_url(protocol, host, port, suffix, explicit_port):
    base_url = f"{protocol}://{host}"
    if explicit_port:
        base_url = f"{base_url}:{port}"
    if suffix:
        base_url = f"{base_url}/{suffix}"
    return base_url


def monitor_get(url, timeout=None):
    return http_probe.monitor_get(url, timeout=timeout)


def monitor_post(url, payload=None, *, headers=None, timeout=None):
    return http_probe.monitor_post(
        url,
        payload,
        headers=headers,
        timeout=timeout,
    )

def monitor_server(address, timeout=None):
    protocol, host, port, suffix = address
    if protocol not in ('http', 'https'):
        protocol = 'http'

    default_port = 80 if protocol == 'http' else 443
    explicit_port = port is not None
    port = port if explicit_port else default_port

    try:
        resolved_timeout = http_probe.resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error("monitor.server.timeout_error host=%s error=%s", host, exc)
        return False

    url = _compose_service_url(protocol, host, port, suffix, explicit_port)

    LOGGER.info("monitor.server.start host=%s port=%s url=%s", host, port, url)

    socket_success = network_probe.check_socket_connectivity(
        host, port, resolved_timeout
    )
    ping_success = network_probe.perform_ping_probe(host, resolved_timeout)
    network_probe.perform_icmp_probe(host, resolved_timeout)

    http_success = http_probe.probe_http_service(url, resolved_timeout)

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
