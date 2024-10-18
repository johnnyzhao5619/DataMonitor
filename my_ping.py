# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 0:56
# @Author: Weijia Zhao
# @File : my_ping.py

import select
import socket
import struct
import time

from typing import Tuple


class my_ping():

    def raw_socket(self, dst_addr: str,
                   icmp_packet: bytes) -> Tuple[float, socket.socket]:
        """
        Sends an ICMP packet to the specified destination address using a raw socket.

        Args:
            dst_addr (str): The destination IP address.
            icmp_packet (bytes): The ICMP packet to be sent.

        Returns:
            Tuple[float, socket.socket]: A tuple containing the time when the request was sent 
            and the raw socket used for sending the packet.
        """
        rawsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                  socket.getprotobyname("icmp"))
        send_request_ping_time = time.time()
        rawsocket.sendto(icmp_packet, (dst_addr, 80))
        return send_request_ping_time, rawsocket

    def checksum(self, data: bytes) -> int:
        """
        Calculates the checksum of the given data.

        Args:
            data (bytes): The data to calculate the checksum for.

        Returns:
            int: The calculated checksum.
        """
        n = len(data)
        m = n % 2
        sum = 0
        for i in range(0, n - m, 2):
            sum += (data[i]) + ((data[i + 1]) << 8)
            sum = (sum >> 16) + (sum & 0xffff)
        if m:
            sum += (data[-1])
            sum = (sum >> 16) + (sum & 0xffff)
        answer = ~sum & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def get_host_address(self, host: str) -> str:
        """
        Get the IP address of a host.

        Args:
            host (str): The hostname to resolve.

        Returns:
            str: The IP address of the host.
        """
        dst_addr = socket.gethostbyname(host)
        return dst_addr

    def request_ping(self, data_type: int, data_code: int, data_checksum: int,
                     data_ID: int, data_Sequence: int,
                     payload_body: bytes) -> bytes:
        """
        Pack the given data into an ICMP packet.

        Args:
            data_type (int): The type of the ICMP message.
            data_code (int): The code of the ICMP message.
            data_checksum (int): The checksum of the ICMP message.
            data_ID (int): The identifier of the ICMP message.
            data_Sequence (int): The sequence number of the ICMP message.
            payload_body (bytes): The payload data for the ICMP message.

        Returns:
            bytes: The packed ICMP packet.
        """
        icmp_packet = struct.pack('>BBHHH32s', data_type, data_code,
                                  data_checksum, data_ID, data_Sequence,
                                  payload_body)
        # Calculate checksum
        icmp_checksum = self.checksum(icmp_packet)
        # Pack with checksum
        icmp_packet = struct.pack('>BBHHH32s', data_type, data_code,
                                  icmp_checksum, data_ID, data_Sequence,
                                  payload_body)
        return icmp_packet

    def reply_ping(
        self,
        send_request_ping_time: float,
        rawsocket: socket.socket,
        data_Sequence: int,
        timeout: float = 3.0,
    ) -> float:
        """
        Calculate the round-trip time for the ICMP echo reply.

        Args:
            send_request_ping_time (float): The time when the ping request was sent.
            rawsocket (socket.socket): The raw socket used for sending and receiving the packet.
            data_Sequence (int): The sequence number of the ICMP packet.
            timeout (float): The maximum time to wait for a response.

        Returns:
            float: The round-trip time for the echo reply, or -1 if the request times out.
        """
        while True:
            # Check if the raw socket is ready to read
            what_ready = select.select([rawsocket], [], [], timeout)
            # Calculate the time waited for a response
            wait_for_time = (time.time() - send_request_ping_time)
            # If no data is ready to be read, return -1
            if what_ready[0] == []:
                return -1.0
            # Record the time when the response was received
            time_received = time.time()
            # Receive the ICMP packet and the sender's address
            received_packet, addr = rawsocket.recvfrom(1024)
            # Extract the ICMP header from the received packet
            icmpHeader = received_packet[20:28]
            # Unpack the ICMP header to extract type, code, checksum, packet ID, and sequence
            type, code, r_checksum, packet_id, sequence = struct.unpack(
                ">BBHHH", icmpHeader)
            # Check if the received packet matches the expected sequence number
            if type == 0 and sequence == data_Sequence:
                return time_received - send_request_ping_time
            # Update the timeout based on the time waited for the response
            timeout = timeout - wait_for_time
            if timeout <= 0:
                return -1.0

    def send_ping(self, address: str) -> int:
        """
        Sends a ping request to the specified address.

        This function sends a ping request to the specified address using an ICMP echo request packet,
        and returns the round-trip time in milliseconds, or -1 if the request times out.

        Args:
            address (str): The address to send the ping request to.

        Returns:
            int: The round-trip time in milliseconds, or -1 if the request times out.
        """
        data_type: int = 8  # ICMP echo request type
        data_code: int = 0  # ICMP echo request code
        data_checksum: int = 0  # ICMP echo request checksum
        data_ID: int = 0  # ICMP echo request ID
        data_Sequence: int = 1  # ICMP echo request sequence number
        payload_body: bytes = b'abcdefghijklmnopqrstuvwabcdefghi'  # ICMP echo request payload
        icmp_packet: bytes = self.request_ping(data_type, data_code,
                                               data_checksum, data_ID,
                                               data_Sequence, payload_body)
        send_request_ping_time: float  # Time when the ping request was sent
        rawsocket: socket.socket  # Raw socket used for sending and receiving the packet
        send_request_ping_time, rawsocket = self.raw_socket(
            address, icmp_packet)
        times: float = self.reply_ping(send_request_ping_time, rawsocket,
                                       data_Sequence)  # Round-trip time
        if times > 0:
            return_time: int = int(times * 1000)  # Convert to milliseconds
            return return_time
        else:
            return -1  # Request timed out
