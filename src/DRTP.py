from struct import *
from socket import *


class DRTP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.header_format = '!IIHH'
        self.seq = 1
        self.socket = socket(AF_INET, SOCK_DGRAM)

    def create_packet(self, seq, ack, flags, win, data):

        header = pack(self.header_format, seq, ack, flags, win)
        print(header)

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

    def client(self, data):
        self.socket.connect
