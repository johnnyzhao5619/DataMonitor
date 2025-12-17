# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: Weijia Zhao
# @File : api_monitor.py

import os
import requests
import socket
import subprocess
import time
from urllib.parse import urlunparse
from typing import Tuple, List, Union, Dict, Optional

from my_ping import my_ping


def _normalize_address(
    address: Tuple[str, Optional[int], str, str]
) -> Dict[str, Union[str, int]]:
    """
    Normalize parsed address tuple into a dict with full URL.
    """
    host, port, path, scheme = address
    default_port = 443 if scheme == 'https' else 80
    port = int(port) if port else default_port
    # Ensure path is safe
    normalized_path = path if path.startswith('/') else f'/{path}' if path else ''
    url = urlunparse((scheme, f"{host}:{port}", normalized_path, '', '', ''))
    return {
        'scheme': scheme,
        'host': host,
        'port': port,
        'path': normalized_path,
        'url': url.rstrip('/')
    }


def monitor_get(address: Dict[str, Union[str, int]],
                headers: Optional[Dict[str, str]] = None
                ) -> Tuple[bool, Dict[str, Union[int, str]]]:
    """
    发送 GET 请求，返回成功与否及详情。
    """
    url = address['url']
    last_error = ''
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, headers=headers or {}, timeout=10)
            code = response.status_code
            if code == 200:
                print(f"{attempt}: GET {url} success")
                return True, {
                    'status_code': code,
                    'body': response.text,
                    'url': url
                }
            last_error = f"HTTP {code}"
            print(f"{attempt}: GET {url} failed with code {code}")
        except Exception as e:
            last_error = str(e)
            print(f"{attempt}: GET {url} failed: {last_error}")
        if attempt < max_attempts - 1:
            time.sleep(2.7)
    return False, {'message': last_error or 'unknown error', 'url': url}


def monitor_post(address: Dict[str, Union[str, int]],
                 payload: Union[str, Dict[str, object]] = "",
                 headers: Optional[Dict[str, str]] = None,
                 use_json: bool = False
                 ) -> Tuple[bool, Dict[str, Union[int, str]]]:
    """
    发送 POST 请求，返回成功与否及详情。
    """
    url = address['url']
    try:
        post_kwargs = {
            "headers": headers or {},
            "timeout": 10,
        }
        if use_json:
            post_kwargs["json"] = payload if payload != "" else {}
        else:
            post_kwargs["data"] = payload or ""
        response = requests.post(url, **post_kwargs)
        code = response.status_code
        if code == 200:
            print(f"POST {url} success")
            return True, {
                'status_code': code,
                'body': response.text,
                'url': url
            }
        print(f"POST {url} failed with code {code}")
        return False, {
            'status_code': code,
            'message': f"HTTP {code}",
            'url': url
        }
    except Exception as e:
        print(f"POST {url} failed: {e}")
        return False, {'message': str(e), 'url': url}


def monitor_server(address: Dict[str, Union[str, int]]
                   ) -> Tuple[bool, Dict[str, str]]:
    """
    使用 socket/ping 检查服务器存活。
    """
    host = address['host']
    port = address['port']
    enable_ping = os.getenv("MONITOR_DISABLE_PING", "0") != "1"
    methods = [('Socket', lambda: check_socket_connection(host, port))]
    if enable_ping:
        methods.append(('Ping', lambda: check_ping(host)))
        # ('ICMP', lambda: check_icmp(address))
    for method_name, method in methods:
        ok, message = method()
        if ok:
            print(f"{host} is online ({method_name})")
            return True, {'method': method_name, 'message': message}

    print(f"{host} is offline")
    return False, {'method': 'SERVER', 'message': 'Offline'}


def check_socket_connection(host: str, port: int) -> Tuple[bool, str]:
    """
    Check if a server is online using a socket connection.

    """
    port = port or 80

    try:
        # Create a socket object
        with socket.create_connection((host, port), timeout=5):
            # If no exception is raised, the connection was successful
            pass
        print(f"{host} is online (Socket)")
        return True, 'Socket connection ok'
    except Exception as e:
        # If an exception is raised, the connection failed
        print(f"Connection to {host}:{port} failed: {e}")
        return False, str(e)


def _system_ping(host: str,
                 fallback_reason: Optional[str] = None) -> Tuple[bool, str]:
    """
    Use OS ping command as a non-privileged fallback.
    """
    cmd = ["ping", "-n", "1", "-w", "1000", host] if os.name == "nt" else [
        "ping", "-c", "1", "-W", "1", host
    ]
    try:
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=3)
        if result.returncode == 0:
            return True, "Ping ok (system)"
        stderr = result.stderr.decode(errors="ignore").strip()
        stdout = result.stdout.decode(errors="ignore").strip()
        msg = stderr or stdout or fallback_reason or "Ping failed"
        return False, msg
    except Exception as e:
        return False, fallback_reason or str(e)


def check_ping(host: str) -> Tuple[bool, str]:
    """
    Check if a server is online using the ping command.
    """
    try:
        ping = my_ping()
        status: List[bool] = []
        data_type: int = 8
        data_code: int = 0
        data_checksum: int = 0
        data_ID: int = 0
        data_Sequence: int = 1
        payload_body: bytes = b'abcdefghijklmnopqrstuvwabcdefghi'
        # Get the IP address of the server
        dst_addr: str = socket.gethostbyname(host)
        print("Pinging {0} [{1}] with 32 bytes of data:".format(
            host, dst_addr))
        # Send 3 times
        for i in range(0, 3):
            # Request a ping data packet
            icmp_packet: bytes = ping.request_ping(data_type, data_code,
                                                   data_checksum, data_ID,
                                                   data_Sequence + i,
                                                   payload_body)
            # Connect a socket and send the data to the socket
            send_request_ping_time, rawsocket = ping.raw_socket(
                dst_addr, icmp_packet)
            # Get the time it took for the data to be sent and received
            times: float = ping.reply_ping(send_request_ping_time, rawsocket,
                                           data_Sequence + i)
            if times > 0:
                print(
                    f"Reply from {dst_addr}: bytes=32 time={int(times * 1000)} ms"
                )
                time.sleep(1.3)
                status.append(True)
            else:
                status.append(False)
                print("Timeout")

        if any(status):
            print(f"{host} is online (Ping)")
            return True, 'Ping ok'
        print(f"{host} is offline (Ping)")
        return False, 'Ping timeout'
    except PermissionError as e:
        # 缺少原始套接字权限时给出可诊断信息
        msg = f"Ping permission denied: {e}"
        print(msg)
        return _system_ping(host, msg)
    except Exception as e:
        msg = str(e)
        print(f"{host} is offline (ICMP): {msg}")
        ok, system_msg = _system_ping(host, msg)
        if ok:
            return True, system_msg
        return False, system_msg


def check_icmp(address: Tuple[str, int, str]) -> Tuple[bool, str]:
    """
    Check if a server is online using ICMP protocol.

    Args:
        address (Tuple[str, int, str]): A tuple containing the host, port, and
        path of the server.

    Returns:
        Tuple[bool, str]: A tuple where the first element is a boolean
        indicating whether the server is online,
        and the second element is a string indicating the method used to check
        the server status.
    """
    host = address[0]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW,
                           socket.IPPROTO_ICMP) as sock:
            # Create a dummy ICMP packet
            dummy_packet = b'\x08\x00\x7d\x4b\x00\x00\x00\x00PingData'
            # Send the ICMP packet to the server
            sock.sendto(dummy_packet, (host, 0))
            # Wait for a response packet
            sock.settimeout(5)
            response_packet = sock.recv(1024)
            print("response_packet:", response_packet)
            # If a response packet is received, the server is online
            print(f"{host} is online (ICMP)")
            return [True, 'ICMP']
    except (socket.timeout, socket.error):
        print(f"{host} is offline (ICMP)")
        pass
