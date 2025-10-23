# -*- codeing = utf-8 -*-
"""网络连通性探测工具函数。"""

import logging
import math
import os
import shutil
import socket
import subprocess
import time
from contextlib import closing

from .icmp_probe import IcmpProbe


LOGGER = logging.getLogger(__name__)


def _subprocess_ping(host: str, timeout: float) -> bool:
    """使用系统 ping 命令进行兜底探测。成功返回 True。"""

    timeout = max(float(timeout), 0.0)
    if os.name == "nt":
        wait_ms = max(int(math.ceil(timeout * 1000)), 1)
        ping_cmd = ["ping", "-n", "1", "-w", str(wait_ms), host]
    else:
        wait_seconds = max(int(math.ceil(timeout)), 1)
        ping_cmd = ["ping", "-c", "1", "-W", str(wait_seconds), host]

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


def check_socket_connectivity(host: str, port: int, timeout: float) -> bool:
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


def perform_ping_probe(host: str, timeout: float, *, attempts: int = 3) -> bool:
    try:
        resolved_timeout = max(float(timeout), 0.0)
    except (TypeError, ValueError):
        LOGGER.warning(
            "monitor.ping.raw.invalid_timeout host=%s timeout=%s", host, timeout
        )
        resolved_timeout = 0.0

    per_attempt_timeout = (
        resolved_timeout / attempts if resolved_timeout > 0 and attempts else 0.0
    )
    sleep_interval = min(per_attempt_timeout, 0.7) if per_attempt_timeout > 0 else 0.0
    remaining_budget = resolved_timeout

    try:
        ping = IcmpProbe()
        status = []
        data_type = 8
        data_code = 0
        data_checksum = 0
        data_id = 0
        data_sequence = 1
        payload_body = b"abcdefghijklmnopqrstuvwabcdefghi"
        dst_addr = socket.gethostbyname(host)
        LOGGER.info(
            "monitor.ping.raw.start host=%s destination=%s payload_size=%s",
            host,
            dst_addr,
            len(payload_body),
        )
        for attempt in range(attempts):
            sequence = data_sequence + attempt
            icmp_packet = ping.request_ping(
                data_type,
                data_code,
                data_checksum,
                data_id,
                sequence,
                payload_body,
            )
            send_request_ping_time, rawsocket_resource = ping.raw_socket(
                dst_addr, icmp_packet
            )
            if not hasattr(rawsocket_resource, "__enter__") or not hasattr(
                rawsocket_resource, "__exit__"
            ):
                rawsocket_resource = closing(rawsocket_resource)

            attempt_timeout = per_attempt_timeout
            if remaining_budget > 0:
                attempt_timeout = min(per_attempt_timeout, remaining_budget)
            else:
                attempt_timeout = 0.0

            with rawsocket_resource as rawsocket:
                times = ping.reply_ping(
                    send_request_ping_time,
                    rawsocket,
                    sequence,
                    timeout=attempt_timeout,
                )
            remaining_budget = max(0.0, remaining_budget - attempt_timeout)
            if times > 0:
                LOGGER.info(
                    "monitor.ping.raw.reply host=%s destination=%s sequence=%s rtt_ms=%s",
                    host,
                    dst_addr,
                    sequence,
                    int(times * 1000),
                )
                status.append(True)
                if sleep_interval > 0 and remaining_budget > 0:
                    sleep_duration = min(sleep_interval, remaining_budget)
                    time.sleep(sleep_duration)
                    remaining_budget = max(0.0, remaining_budget - sleep_duration)
            else:
                status.append(False)
                LOGGER.warning(
                    "monitor.ping.raw.timeout host=%s destination=%s sequence=%s",
                    host,
                    dst_addr,
                    sequence,
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
    except Exception as exc:  # pragma: no cover - defensive safeguard
        LOGGER.warning("monitor.ping.raw.error host=%s error=%s", host, exc)
        return _subprocess_ping(host, timeout)


def perform_icmp_probe(host: str, timeout: float) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            dummy_packet = b"\x08\x00}\x4b\x00\x00\x00\x00PingData"
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


__all__ = [
    "check_socket_connectivity",
    "perform_icmp_probe",
    "perform_ping_probe",
]

