from struct import *
from socket import *
import sys
import time


class DRTP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.header_format = '!IIHH'
        self.seq = 1
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.timeout = 0.5

    def create_packet(self, seq, ack, flags, win, data):
        header = pack(self.header_format, seq, ack, flags, win)
        packet = header + data
        return packet

    def parse_header(self, header):
        header_from_msg = unpack(self.header_format, header)
        return header_from_msg

    def parse_flags(self, flags):
        syn = flags & (1 << 3)
        ack = flags & (1 << 2)
        fin = flags & (1 << 1)
        return syn, ack, fin

    def connect(self):
        self.socket.connect((self.ip, self.port))

        sync = self.create_packet(self.seq, 0, 8, 0, b'')
        self.socket.settimeout(0.5)

        # start_time = time.time()
        self.socket.send(sync)
        try:
            ret = self.socket.recv(1472)
        except:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        # end_time = time.time()

        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)
        if syn == 0 or ackflag == 0 or seq != self.seq:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()
        end_time = time.time()

        # self.timeout = int((end_time-start_time)*4)
        # self.socket.settimeout(self.timeout)
        try:

            self.socket.send(self.create_packet(
                0, 1, 4, 0, b''))
        except:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        self.seq += 1

    def bind(self):
        try:
            self.socket.bind((self.ip, self.port))
        except:
            sys.exit()

        sync, self.client = self.socket.recvfrom(1472)
        self.socket.settimeout(0.5)

        header = sync[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        if syn == 0:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        sync = self.create_packet(self.seq, 0, 12, 0, b'')

        try:
            self.socket.sendto(sync, self.client)
        except:
            self.socket.close()
            print("ERROR. Synchronize failed")
            sys.exit()

        ret = b''

        try:
            ret = self.socket.recv(1472)

        except:
            self.socket.close()
            print("ERROR. Synchronize failed")
            sys.exit()

        header = ret[:12]
        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        if self.seq != ack or ackflag == 0:
            self.socket.close()
            print("ERROR. Synchronize failed")

        self.seq += 1

    def close(self):

        while True:
            fin = self.create_packet(self.seq, 0, 2, 0, b'')

            self.socket.send(fin)
            try:
                ret = self.socket.recv(1472)
            except:
                continue

            header = ret[:12]

            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if self.seq == ack or ackflag != 0:
                break

        self.socket.close()

    def stop_and_wait_sender(self, data):

        while True:
            self.socket.send(self.create_packet(self.seq, 0, 0, 0, data))
            try:
                ret = self.socket.recv(1472)
            except:
                continue

            header = ret[:12]

            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if self.seq == ack or ackflag != 0:
                break

        self.seq += 1

    def stop_and_wait_receiver(self):
        while True:
            try:
                ret = self.socket.recv(1472)
            except:
                continue
            break

        msg = ret[12:]
        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        self.socket.sendto(
            self.create_packet(0, seq, 4, 0, b''), self.client
        )

        if fin != 0:
            self.socket.close()
            return 'fin'
        elif (self.seq == seq):
            self.seq += 1
            return msg[12:]
