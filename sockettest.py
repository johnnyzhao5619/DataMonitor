# -*- codeing = utf-8 -*-
# @Time : 2023-03-31 3:42 p.m.
# @Author: weijiazhao
# @File : sockettest.py
# @Software: PyCharm
import socket
import ping3
from scapy.all import *

server = "example.com"  # Replace with the server hostname or IP address

try:
    response = sr1(IP(dst=server) / ICMP(), timeout=1, verbose=0)
    if response:
        print("Server is online and responding")
    else:
        print("Server is online but not responding to ICMP requests")

except:
    print("Server is offline or not responding")




def socket_test(name, server, port):
    try:
        with socket.create_connection((server, port), timeout=5) as sock:
            print(sock)
            print("{} server is up and running!".format(name))

    except socket.error as e:
        print("An error occurred while checking the {} server status:".format(name), e)


def find_port(name, server):
    open_port = []
    ports = range(1, 1025)  # Scan the first 1024 port numbers

    for port in ports:
        try:
            with socket.create_connection((server, port), timeout=1) as sock:
                print("Port {} is open".format(port))
                open_port.append(port)

        except socket.error:
            print("Port {} is closed".format(port))
            pass  # Port is closed or not responding

    print("{} server's port scanning complete".format(name))
    print("Open Port({} server):".format(name), open_port)


def ping_test(name, server):
    try:
        response_time = ping3.ping(server, timeout=2)

        if response_time is not None:
            print("{} server is online - response time: {} ms".format(name, response_time))
        else:
            print("{} server is offline".format(name, response_time))

    except ping3.exceptions.PingError as e:
        print("An error occurred while checking {} server status:".format(name, response_time), e)



# wuxi
server_wuxi = "36.155.95.59"  # Replace with the server hostname or IP address
port_wuxi = 28080  # Replace with the port number of the service to check


# nanjing
server_nanjing = "101.132.145.141"  # Replace with the server hostname or IP address
port_nanjing = 42887 # Replace with the port number of the service to check

# Wuhan
server_wuhan = "c2v.huali-cloud.com"  # Replace with the server hostname or IP address
port_wuhan = 80  # Replace with the port number of the service to check



# find_port('Wuxi', port_wuxi)
# find_port('Nanjing', port_nanjing)
# find_port('Wuhan', port_wuhan)

socket_test('Wuxi', server_wuxi, port_wuxi)
socket_test('Nanjing', server_nanjing, port_nanjing)
socket_test('Wuhan', server_wuhan, port_wuhan)

ping_test('Wuxi', server_wuxi)
ping_test('Nanjing', server_nanjing)
ping_test('Wuhan', server_wuhan)