# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : apiMonitor.py
# @Software: PyCharm
import os
import socket
import subprocess
import time
import requests
from myPing import *


def monitor_get(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"GET request to {url} successful")
            return True
        else:
            print(f"GET request to {url} failed with status code: {response.status_code}")
            return False
    except:
        print(f"GET request to {url} failed")
        return False



def monitor_post(url, payload):
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"POST request to {url} successful")
            return True
        else:
            print(f"POST request to {url} failed with status code: {response.status_code}")
            return False
    except:
        print(f"POST request to {url} failed")
        return False

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



def monitor_server(address):
    host = address[0]
    if(address[1] == '' and address[2] == '' ):
        url = 'https://' + address[0]
        port = 80
    elif(address[1] != '' and address[2] == ''):
        url = 'https://' + address[0] + ':' + str(address[1])
        port = address[1]
    elif(address[1] != '' and address[2] != ''):
        url = 'https://' + address[0] + ':' + str(address[1]) + '/' + address[2]
        port = address[1]
    elif (address[1] == '' and address[2] != ''):
        url = 'https://' + address[0] + '/' + address[2]
        port = 80
    print("host:", host)
    print("port:", port)
    print("url:", url)

    try:
        # Method 1: Use socket to connect to a well-known port
        with socket.create_connection((host, port), timeout=5):
            pass
        print(f"{host} is online (Socket)")
    except (ConnectionRefusedError, socket.timeout):
        print(f"{host} is offline (Socket)")
        pass

    # Ping
    # try:
    #     # Method 2: Use subprocess to send a ping request
    #     subprocess.check_output(['ping', '-c', '1', '-W', '5', host])
    #     print(f"{host} is online (Ping)")
    #     return True
    # except subprocess.CalledProcessError:
    #     print(f"{host} is offline (Ping)")
    #     pass
    #
    # try:
    #     with socket.create_connection((host, port), timeout=5):
    #         print(f"{host} is online (Ping)")
    #         return True
    # except OSError:
    #     print(f"{host} is offline (Ping)")
    #     pass

    try:
        # Method 2: Use subprocess to send a ping request
        # 使用Ping方法
        ping = MyPing()
        status = []
        sumtime, shorttime, longtime, avgtime = 0, 1000, 0, 0
        # 8回射请求 11超时 0回射应答
        data_type = 8
        data_code = 0
        # 检验和
        data_checksum = 0
        # ID
        data_ID = 0
        # 序号
        data_Sequence = 1
        # 可选的内容
        payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'
        dst_addr = socket.gethostbyname(host)
        print("正在 Ping {0} [{1}] 具有 32 字节的数据:".format(host, dst_addr))
        # 发送3次
        for i in range(0, 3):
            # 请求ping数据包的二进制转换
            icmp_packet = ping.request_ping(data_type, data_code, data_checksum, data_ID, data_Sequence + i,
                                            payload_body)
            # 连接套接字,并将数据发送到套接字
            send_request_ping_time, rawsocket = ping.raw_socket(dst_addr, icmp_packet)
            # 数据包传输时间
            times = ping.reply_ping(send_request_ping_time, rawsocket, data_Sequence + i)
            if times > 0:
                print("来自 {0} 的回复: 字节=32 时间={1}ms".format(dst_addr, int(times * 1000)))
                return_time = int(times * 1000)
                sumtime += return_time
                if return_time > longtime:
                    longtime = return_time
                if return_time < shorttime:
                    shorttime = return_time
                time.sleep(0.7)
                status.append(True)
            else:
                status.append(False)
                print("请求超时")

        if any(status):
            print(f"{host} is online (Ping)")
        else:
            print(f"{host} is offline (Ping)")
            pass

    except subprocess.CalledProcessError:
        print(f"{host} is offline (Ping)")
        pass


    # ICMP
    try:
        # Method 3: Use ICMP request to check if server responds
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            # Create a dummy ICMP packet
            dummy_packet = b'\x08\x00\x7d\x4b\x00\x00\x00\x00PingData'
            # Send the ICMP packet to the server
            sock.sendto(dummy_packet, (host, 0))
            # Wait for a response packet
            sock.settimeout(5)
            response_packet = sock.recv(1024)
            # If a response packet is received, the server is online
            print(f"{host} is online (ICMP)")
    except (socket.timeout, socket.error):
        print(f"{host} is offline (ICMP)")
        pass

    # request
    http_success = None
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        if 200 <= status_code < 400:
            print(f"{url} responded with status code {status_code} (Get Requests)")
            http_success = True
        else:
            print(f"{url} returned status code {status_code} (Get Requests)")
            http_success = False
    except requests.RequestException as exc:
        print(f"{url} request failed (Get Requests): {exc}")
        http_success = False

    if http_success:
        return True

    # If HTTP check fails, consider server offline regardless of lower-level reachability
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