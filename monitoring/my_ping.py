# -*- codeing = utf-8 -*-
# @Time : 2023/4/10 0:56
# @Author: weijia
# @File : my_ping.py
# @Software: PyCharm

import time, struct
import socket, select
from contextlib import closing

class MyPing():
    # Send the raw ICMP packet through a socket.
    def raw_socket(self, dst_addr, imcp_packet):
        rawsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
        send_request_ping_time = time.time()
        rawsocket.sendto(imcp_packet, (dst_addr, 80))
        return send_request_ping_time, closing(rawsocket)

    # Calculate the checksum for an ICMP payload.
    def chesksum(self, data):
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

    # Resolve the destination host address from a hostname.
    def get_host_address(self,host):
        dst_addr = socket.gethostbyname(host)
        return dst_addr

    # Construct an ICMP echo request packet.
    def request_ping(self, data_type, data_code, data_checksum, data_ID, data_Sequence, payload_body):
        # Pack the supplied fields into a binary structure.
        imcp_packet = struct.pack('>BBHHH32s', data_type, data_code, data_checksum, data_ID, data_Sequence,payload_body)
        # Calculate the checksum based on the initial packet.
        icmp_chesksum = self.chesksum(imcp_packet)
        # Insert the checksum and rebuild the packet bytes.
        imcp_packet = struct.pack('>BBHHH32s', data_type, data_code, icmp_chesksum, data_ID, data_Sequence,payload_body)
        return imcp_packet

    # Process reply packets by unpacking and validating them.
    def reply_ping(self, send_request_ping_time, rawsocket, data_Sequence, timeout=3):
        while True:
            # Wait for the raw socket to become readable within the timeout window.
            what_ready = select.select([rawsocket], [], [], timeout)
            # Track how much time was spent waiting in this iteration.
            wait_for_time = (time.time() - send_request_ping_time)
            # Treat a lack of readable sockets as a timeout event.
            if what_ready[0] == []:
                return -1
            # Record when the response was received.
            time_received = time.time()
            # Read up to 1024 bytes from the raw socket.
            received_packet, addr = rawsocket.recvfrom(1024)
            # Extract the ICMP header from the response payload.
            icmpHeader = received_packet[20:28]
            # Decode the header fields into their native values.
            type, code, r_checksum, packet_id, sequence = struct.unpack(">BBHHH", icmpHeader)
            if type == 0 and sequence == data_Sequence:
                return time_received - send_request_ping_time
            # Update the remaining timeout budget and abort if it is exhausted.
            timeout = timeout - wait_for_time
            if timeout <= 0:
                return -1

    # Send a ping command to the specified address.
    def send_ping(self, address, timeout=None):
        data_type = 8
        data_code = 0
        data_checksum = 0
        data_ID = 0
        data_Sequence = 1
        payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'

        # Build the binary representation of the ping request.
        icmp_packet = self.request_ping(data_type, data_code, data_checksum, data_ID, data_Sequence, payload_body)
        # Open the raw socket context and send the packet through it.
        send_request_ping_time, rawsocket_context = self.raw_socket(address, icmp_packet)
        if not hasattr(rawsocket_context, "__enter__") or not hasattr(rawsocket_context, "__exit__"):
            rawsocket_context = closing(rawsocket_context)

        with rawsocket_context as rawsocket:
            # Measure the round-trip time for the response packet.
            reply_kwargs = {}
            if timeout is not None:
                reply_kwargs["timeout"] = timeout
            times = self.reply_ping(send_request_ping_time, rawsocket, data_Sequence, **reply_kwargs)
        if times > 0:
            return_time = int(times * 1000)
            return return_time
        else:
            return -1
