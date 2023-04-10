# -*- codeing = utf-8 -*-
# @Time : 2023-03-29 3:23 p.m.
# @Author: weijiazhao
# @File : apiMonitor.py
# @Software: PyCharm
import os
import socket
import subprocess


import requests

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
        url = 'http://' + address[0]
        port = 80
    elif(address[1] != '' and address[2] == ''):
        url = 'http://' + address[0] + ':' + str(address[1])
        port = address[1]
    elif(address[1] != '' and address[2] != ''):
        url = 'http://' + address[0] + ':' + str(address[1]) + '/' + address[2]
        port = address[1]
    print("host:", host)
    print("port:", port)
    print("url:", url)

    try:
        # Method 1: Use socket to connect to a well-known port
        with socket.create_connection((host, 80), timeout=5):
            pass  # If no exception is raised, the connection was successful
        print(f"{host} is online (Socket)")
        return True
    except (ConnectionRefusedError, socket.timeout):
        print(f"{host} is offline (Socket)")
        pass

    # Ping
    try:
        # Method 2: Use subprocess to send a ping request
        subprocess.check_output(['ping', '-c', '1', '-W', '5', host])
        print(f"{host} is online (Ping)")
        return True
    except subprocess.CalledProcessError:
        print(f"{host} is offline (Ping)")
        pass

    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"{host} is online (Ping)")
            return True
    except OSError:
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
            return True
    except (socket.timeout, socket.error):
        print(f"{host} is offline (ICMP)")
        pass

    # request
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"{url} is online (Get Requests)")
            print(response)
            return True
        else:
            print(f"{url} is offline (Get Requests)")
            return True
    except:
        print(f"{url} is offline (Get Requests)")
        pass

    # If none of the methods succeed, the server is offline
    print(f"{host} is offline")
    return False


