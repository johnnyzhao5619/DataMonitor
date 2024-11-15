# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: Weijia Zhao
# @File : api_monitor.py

import requests
import socket
import time
from typing import Tuple, List, Union

from my_ping import my_ping


def monitor_get(
        url_parts: Tuple[str, str, str]) -> Tuple[bool, Union[str, int]]:
    """
    Send a GET request to the url and return True if the request is successful.

    Args:
        url_parts (Tuple[str, str, str]): A tuple containing the host, port,
        and path of the url.

    Returns:
        A tuple containing a boolean indicating whether the request is
        successful and a string or integer describing the result.
    """
    retry_count = 0
    url = f"https://{url_parts[0]}:{url_parts[1] if url_parts[1] else '80'}/{url_parts[2] if url_parts[2] else ''}".rstrip(
        '/')
    while retry_count < 2:
        try:
            response = requests.get(url, timeout=10)
            code = response.status_code
            message = f"{retry_count}: GET request to {url}"
            if code == 200:
                print(f"{message} successful")
                return True, code
            else:
                print(f"{message} failed with status code: {code}")
                return False, code
        except Exception as e:
            print(f"{retry_count}: GET request to {url} failed: {e}")
            feedback = str(e)
        retry_count += 1
        time.sleep(2.7)
    return False, feedback


def monitor_post(url: str, payload: str) -> Tuple[bool, Union[str, int]]:
    """
    Send a POST request to the url with the given payload and return True 
    if the request is successful.

    Args:
        url (str): The url to send the request to.
        payload (str): The payload to send with the request.

    Returns:
        Tuple[bool, Union[str, int]]: A tuple containing a boolean indicating whether the request is
        successful and a string or integer describing the result.
    """
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    try:
        response = requests.post(url, data=payload)
        code = response.status_code
        if code == 200:
            print(f"POST request to {url} successful")
            return True, code
        else:
            print(
                f"POST request to {url} failed with status code: {response.code}"
            )
            return False, code
    except Exception as e:
        print(f"POST request to {url} failed: {e}")
        feedback = str(e)
        return False, feedback


def monitor_server(address: tuple[str, int, str]) -> tuple[bool, str]:
    """
    Check if a server is online using multiple methods.

    Args:
        address: A tuple containing the host, port, and path of the server.

    Returns:
        A tuple where the first element is a boolean indicating whether the
        server is online, and the second element is a string indicating the
        method used to check the server status.
    """
    feedback = 'SERVER'
    # Define the methods to check server status
    methods = [
        ('Socket', lambda: check_socket_connection(address)),
        ('Ping', lambda: check_ping(address)),
        # ('ICMP', lambda: check_icmp(address))
    ]
    # Extract host, port, and path from the address
    host, port, path = address
    default_port = 80
    port = port or default_port
    # Loop through the methods and check server status
    for method_name, method in methods:
        if method():
            print(f"{host} is online ({method_name})")
            return True, method_name

    print(f"{host} is offline")
    return False, feedback


def check_socket_connection(address: Tuple[str, int, str]) -> bool:
    """
    Check if a server is online using a socket connection.

    Args:
        address: A tuple containing the host, port and path of the server.

    Returns:
        A boolean indicating whether the server is online.
    """
    print(">>>>>url:", address)

    host, port, _ = address
    port = port or 80

    try:
        # Create a socket object
        with socket.create_connection((host, port), timeout=5):
            # If no exception is raised, the connection was successful
            pass
        print(f"{host} is online (Socket)")
        return [True, 'Socket']
    except Exception as e:
        # If an exception is raised, the connection failed
        print(f"Connection to {host}:{port} failed: {e}")
        pass


def check_ping(address: Tuple[str, int, str]) -> Tuple[bool, str]:
    """
    Check if a server is online using the ping command.

    Args:
        address: A tuple containing the host, port and path of the server.

    Returns:
        A tuple where the first element is a boolean indicating whether the
        server is online, and the second element is a string indicating the
        method used to check the server status.
    """
    host = address[0]
    try:
        ping = my_ping()
        status: List[bool] = []
        sumtime, shorttime, longtime, avgtime = 0, 1000, 0, 0
        data_type: int = 8
        data_code: int = 0
        # Checksum
        data_checksum: int = 0
        # ID
        data_ID: int = 0
        # Sequence
        data_Sequence: int = 1
        # Option
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
                return_time: int = int(times * 1000)
                sumtime += return_time
                if return_time > longtime:
                    longtime = return_time
                if return_time < shorttime:
                    shorttime = return_time
                time.sleep(1.3)
                status.append(True)
            else:
                status.append(False)
                print("Timeout")

        if any(status):
            print(f"{host} is online (Ping)")
            return [True, 'Ping']
        else:
            print(f"{host} is offline (Ping)")
            pass
    except Exception as e:
        print(f"{host} is offline (ICMP): {e}")
        pass


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
