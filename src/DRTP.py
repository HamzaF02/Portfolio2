from struct import *
from socket import *
import time


class DRTP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.header_format = '!IIHH'
        self.seq = 1
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.timeout = 500
        self.socket.settimeout(self.timeout)

    def create_packet(self, seq, ack, flags, win, data):
        header = pack(self.header_format, seq, ack, flags, win)
        packet = header + data
        return packet

    def parse_header(self, header):
        header_from_msg = unpack(self.header_format, header)
        return header_from_msg

    def parse_flags(flags):
        syn = flags & (1 << 3)
        ack = flags & (1 << 2)
        fin = flags & (1 << 1)
        return syn, ack, fin

    def connect(self):
        self.socket.connect((self.ip, self.port))
        start_time = time.time()
        self.stop_and_wait(
            self.create_packet(self.seq, 0, 8, 0, 0, '')
        )
        end_time = time.time()

        self.socket.recv()

        seq, ack, flags, win = self.recv()

    # def recv(self):
    #     msg = self.socket.recv(1024)
    #     seq, ack, flags, win = self.parse_header(msg[:12])
    #     return seq, ack, flags, win

    def stop_and_wait_sender(self, data):
        self.socket.send(data)
        ret = self.socket.recv(1024)

        ############# RESET TIMER!!! ##############

        if ret is None:
            self.stop_and_wait_sender(data)
            return

        msg = ret[12:]
        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]

        if self.seq != ack:
            self.stop_and_wait_sender(data)

        self.seq += 1

    def stop_and_wait_receiver(self, data):
        ret = self.socket.recv(1024)

        if ret is not None:
            self.socket.send(
                self.create_packet(0, seq, 4, 0, 0, '')
            )
        msg = ret[12:]
        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]

        if (self.seq == seq):
            self.seq += 1
            return msg
