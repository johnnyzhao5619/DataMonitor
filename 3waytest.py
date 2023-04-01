# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 4:37 p.m.
# @Author: weijiazhao
# @File : 3waytest.py
# @Software: PyCharm

import socket
import subprocess

import requests


def is_server_online(address):
    host = address[0]
    if(len(address) == 1):
        url = 'http://' + address[0]
    elif(len(address) == 2):
        url = 'http://' + address[0] + ':' + str(address[1])
    elif(len(address) == 3):
        url = 'http://' + address[0] + ':' + str(address[1]) + address[2]

    try:
        # Method 1: Use socket to connect to a well-known port
        with socket.create_connection((host, 80), timeout=5):
            pass  # If no exception is raised, the connection was successful
        print(f"{host} is online (Socket)")
        return True
    except (ConnectionRefusedError, socket.timeout):
        print(f"{host} is offline (Socket)")
        pass

    try:
        # Method 2: Use subprocess to send a ping request
        subprocess.check_output(['ping', '-c', '1', '-W', '2', host])
        print(f"{host} is online (Ping)")
        return True
    except subprocess.CalledProcessError:
        print(f"{host} is offline (Ping)")
        pass

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
            return True
    except (socket.timeout, socket.error):
        print(f"{host} is offline (ICMP)")
        pass

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"{url} is online (Get Requests)")
            print(response)
            return True
        else:
            print(f"{url} is offline (Get Requests)")
            return False
    except:
        print(f"{url} is offline (Get Requests)")
        return False

    # If none of the methods succeed, the server is offline
    print(f"{host} is offline")
    return False

# wuxi
server_wuxi = ['36.155.95.59', 28080, '/JKS_Server/SysInfo']  # Replace with the server hostname or IP address

# nanjing
server_nanjing = ["101.132.145.141", 42887]  # Replace with the server hostname or IP address

# Wuhan
server_wuhan = ["c2v.huali-cloud.com", 80]  # Replace with the server hostname or IP address


# a = is_server_online(server_wuxi)
# a = is_server_online(server_nanjing)
a =  is_server_online(server_wuhan)

print(a)