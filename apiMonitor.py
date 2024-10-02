# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : apiMonitor.py

import requests
import subprocess
import socket
import time

from myPing import MyPing


def monitor_get(url):
    check = 0
    if (url[1] == '' and url[2] == ''):
        url = 'http://' + url[0]
    elif (url[1] != '' and url[2] == ''):
        url = 'http://' + url[0] + ':' + str(url[1])
    elif (url[1] != '' and url[2] != ''):
        url = 'http://' + url[0] + ':' + str(url[1]) + '/' + url[2]
    elif (url[1] == '' and url[2] != ''):
        url = 'http://' + url[0] + '/' + url[2]
    # 当相应失败时，再次尝试，如果两次都失败时，返回False
    while check < 2:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"{check}: GET request to {url} successful")
                return True, response.text
            else:
                print(
                    f"{check}: GET request to {url} failed with status code: {response.status_code}"
                )
                feedback = response.status_code
                check += 1
                # return False, response.status_code
        except:
            print(f"{check}: GET request to {url} failed")
            feedback = 'GET'
            check += 1
        time.sleep(2.7)
    return False, feedback


def monitor_post(url, payload):
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"POST request to {url} successful")
            return True, response.text
        else:
            print(
                f"POST request to {url} failed with status code: {response.status_code}"
            )
            feedback = response.status_code
            return False, feedback
    except:
        print(f"POST request to {url} failed")
        feedback = 'GET'
        return False, feedback


def monitor_server(address):
    host = address[0]
    if (address[1] == '' and address[2] == ''):
        url = 'https://' + address[0]
        port = 80
    elif (address[1] != '' and address[2] == ''):
        url = 'https://' + address[0] + ':' + str(address[1])
        port = address[1]
    elif (address[1] != '' and address[2] != ''):
        url = 'https://' + address[0] + ':' + str(
            address[1]) + '/' + address[2]
        port = address[1]
    elif (address[1] == '' and address[2] != ''):
        url = 'https://' + address[0] + '/' + address[2]
        port = 80

    try:
        # Method 1: Use socket to connect to a well-known port
        with socket.create_connection((host, port), timeout=5):
            pass  # If no exception is raised, the connection was successful
        print(f"{host} is online (Socket)")
        return True, 'Socket'
    except (ConnectionRefusedError, socket.timeout):
        print(f"{host} is offline (Socket)")
        pass

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
        print("Pinging {0} [{1}] with 32 bytes of data:".format(
            host, dst_addr))
        # 发送3次
        for i in range(0, 5):
            # 请求ping数据包的二进制转换
            icmp_packet = ping.request_ping(data_type, data_code,
                                            data_checksum, data_ID,
                                            data_Sequence + i, payload_body)
            # 连接套接字,并将数据发送到套接字
            send_request_ping_time, rawsocket = ping.raw_socket(
                dst_addr, icmp_packet)
            # 数据包传输时间
            times = ping.reply_ping(send_request_ping_time, rawsocket,
                                    data_Sequence + i)
            if times > 0:
                print("Reply from {0}: bytes=32 time={1}ms".format(
                    dst_addr, int(times * 1000)))
                return_time = int(times * 1000)
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
            return True, 'Ping'
        else:
            print(f"{host} is offline (Ping)")
            pass
    except subprocess.CalledProcessError:
        print(f"{host} is offline (Ping)")
        pass

    # ICMP
    try:
        # Method 3: Use ICMP request to check if server responds
        with socket.socket(socket.AF_INET, socket.SOCK_RAW,
                           socket.IPPROTO_ICMP) as sock:
            # Create a dummy ICMP packet
            dummy_packet = b'\x08\x00\x7d\x4b\x00\x00\x00\x00PingData'
            # Send the ICMP packet to the server
            sock.sendto(dummy_packet, (host, 0))
            # Wait for a response packet
            sock.settimeout(5)
            response_packet = sock.recv(1024)
            # If a response packet is received, the server is online
            print(f"{host} is online (ICMP)")
            return True, 'ICMP'
    except (socket.timeout, socket.error):
        print(f"{host} is offline (ICMP)")
        pass

    # If none of the methods succeed, the server is offline
    print(f"{host} is offline")
    return [False, 'SERVER']
