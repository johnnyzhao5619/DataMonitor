# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : apiMonitor.py
# @Software: PyCharm
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
        print(f"警告: 系统未找到 ping 命令，跳过子进程 Ping 检测。")
        return False

    try:
        subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT)
        print(f"{host} is online (Subprocess Ping)")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"{host} is offline (Subprocess Ping): {exc}")
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
        print(f"{method_name} request to {url} failed with error: {exc}")
        return False

    if 200 <= response.status_code < 400:
        print(
            f"{method_name} request to {url} successful with status code: {response.status_code}"
        )
        return True

    print(
        f"{method_name} request to {url} failed with status code: {response.status_code}"
    )
    return False


def monitor_get(url, timeout=None):
    try:
        resolved_timeout = _resolve_timeout(timeout)
    except ValueError as exc:
        print(f"GET request to {url} failed with error: {exc}")
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
        print(f"POST request to {url} failed with error: {exc}")
        return False
    return _perform_http_request(
        "POST",
        requests.post,
        url,
        timeout=resolved_timeout,
        payload=payload,
        headers=headers,
    )

# def monitor_server(host: str, timeout: float = 2.0) -> bool:
#     try:
#         response_time = ping3.ping(host, timeout=timeout)
#         if response_time is not None:
#             print("response_time:", response_time)
#             return True, response_time
#         else:
#             return False, "Unknow Error"
#     except ping3.NetworkError:
#         print(f"Network error: Could not reach host {host}")
#         return False, f"Network error: Could not reach host {host}"
#     except ping3.Timeout:
#         print(f"Timeout error: Host {host} did not respond within {timeout} seconds")
#         return False, f"Timeout error: Host {host} did not respond within {timeout} seconds"
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False, f"An error occurred: {e}"



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
        print(f"{host} is online (Socket)")
        return True
    except OSError as exc:
        print(f"{host} is offline (Socket): {exc}")
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
        print("正在 Ping {0} [{1}] 具有 32 字节的数据:".format(host, dst_addr))
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
                print("来自 {0} 的回复: 字节=32 时间={1}ms".format(dst_addr, int(times * 1000)))
                status.append(True)
                time.sleep(0.7)
            else:
                status.append(False)
                print("请求超时")

        success = any(status)
        if success:
            print(f"{host} is online (Ping)")
        else:
            print(f"{host} is offline (Ping)")
        return success
    except (PermissionError, OSError) as exc:
        print(f"警告: 原始 Ping 需要管理员权限或发生套接字错误，已跳过。详情: {exc}")
        return _subprocess_ping(host, timeout)
    except Exception as exc:
        print(f"警告: 原始 Ping 发生未知异常，尝试回退子进程 Ping。详情: {exc}")
        return _subprocess_ping(host, timeout)


def _perform_icmp_probe(host, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            dummy_packet = b'\x08\x00\x7d\x4b\x00\x00\x00\x00PingData'
            sock.sendto(dummy_packet, (host, 0))
            sock.settimeout(timeout)
            sock.recv(1024)
            print(f"{host} is online (ICMP)")
            return True
    except PermissionError as exc:
        print(f"警告: 原始 ICMP 检测需要管理员权限，已跳过。详情: {exc}")
    except (socket.timeout, socket.error) as exc:
        print(f"{host} is offline (ICMP): {exc}")
    return False


def _perform_http_probe(url, timeout):
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        print(f"{url} request failed (Get Requests): {exc}")
        return False

    status_code = response.status_code
    if 200 <= status_code < 400:
        print(f"{url} responded with status code {status_code} (Get Requests)")
        return True

    print(f"{url} returned status code {status_code} (Get Requests)")
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
        print(f"{host} request failed: {exc}")
        return False

    url = _compose_service_url(protocol, host, port, suffix, explicit_port)

    print("host:", host)
    print("port:", port)
    print("url:", url)

    socket_success = _check_socket_connectivity(host, port, resolved_timeout)
    ping_success = _perform_ping_probe(host, resolved_timeout)
    _perform_icmp_probe(host, resolved_timeout)

    http_success = _perform_http_probe(url, resolved_timeout)

    print(
        f"探测结果: socket={socket_success}, ping={ping_success}, http={http_success}"
    )

    if http_success:
        return True

    if socket_success or ping_success:
        print(f"{host} 网络层可达，但 HTTP 检测失败，返回回退成功。")
        return True

    print(f"{host} is offline")
    return False



# while True:
#     host = "c2v.huali-cloud.com"
#     port = 80
#
#     # 使用Ping方法
#     ping = MyPing()
#     status = []
#     sumtime, shorttime, longtime, avgtime = 0, 1000, 0, 0
#     # 8回射请求 11超时 0回射应答
#     data_type = 8
#     data_code = 0
#     # 检验和
#     data_checksum = 0
#     # ID
#     data_ID = 0
#     # 序号
#     data_Sequence = 1
#     # 可选的内容
#     payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'
#     dst_addr = socket.gethostbyname(host)
#     print("正在 Ping {0} [{1}] 具有 32 字节的数据:".format(host, dst_addr))
#     # 发送3次
#     for i in range(0, 3):
#         # 请求ping数据包的二进制转换
#         icmp_packet = ping.request_ping(data_type, data_code, data_checksum, data_ID, data_Sequence + i,
#                                         payload_body)
#         # 连接套接字,并将数据发送到套接字
#         send_request_ping_time, rawsocket = ping.raw_socket(dst_addr, icmp_packet)
#         # 数据包传输时间
#         times = ping.reply_ping(send_request_ping_time, rawsocket, data_Sequence + i)
#         if times > 0:
#             print("来自 {0} 的回复: 字节=32 时间={1}ms".format(dst_addr, int(times * 1000)))
#             return_time = int(times * 1000)
#             sumtime += return_time
#             if return_time > longtime:
#                 longtime = return_time
#             if return_time < shorttime:
#                 shorttime = return_time
#             time.sleep(0.7)
#             status.append(True)
#         else:
#             status.append(False)
#             print("请求超时")
#     print("status:", status)
#     if any(status):
#         print(f"{host} is online (Ping)")
#     else:
#         print(f"{host} is offline (Ping)")
#
#     time.sleep(5)