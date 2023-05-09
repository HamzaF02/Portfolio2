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
        server = (self.ip, self.port)

        sync = self.create_packet(self.seq, 0, 8, 0, b'')

        start_time = time.time()
        self.socket.sendto(sync, (self.ip, self.port))
        ret = self.socket.recv(2048)
        end_time = time.time()

        if ret is None:
            print("ERROR. Synchronize acknowledgment not received")
            self.socket.close()
            sys.exit()

        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)
        if syn == 0 or ackflag == 0 or seq != self.seq:
            print("ERROR. Synchronize acknowledgment not received")
            self.socket.close()
            sys.exit()
        end_time = time.time()

        self.timeout = int((end_time-start_time)*4)
        # self.socket.settimeout(self.timeout)

        self.socket.sendto(self.create_packet(
            0, 1, 4, 0, b''), (self.ip, self.port))
        self.seq += 1

    def bind(self):
        try:
            self.socket.bind((self.ip, self.port))
        except:
            sys.exit()

        sync, self.client = self.socket.recvfrom(2048)
        header = sync[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        if syn == 0:
            print("ERROR. Synchronize not received")
            self.socket.close()
            sys.exit()

        sync = self.create_packet(self.seq, 0, 12, 0, b'')

        self.socket.sendto(sync, self.client)
        ret = self.socket.recv(1024)

        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        if self.seq != ack or ackflag == 0:
            print("ERROR. Acknowledgement of Acknowledgement of Synchronize not received")
            self.socket.close()
            sys.exit()
        self.seq += 1

    def close(self):

        while True:
            fin = self.create_packet(self.seq, 0, 2, 0, b'')

            self.socket.sendto(fin, (self.ip, self.port))

            ret = self.socket.recv(2048)

            if ret is None:
                continue

            header = ret[:12]

            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if self.seq == ack or ackflag != 0:
                break

        self.socket.close()

    def stop_and_wait_sender(self, data):
        self.socket.sendto(self.create_packet(
            self.seq, 0, 0, 0, data), (self.ip, self.port))
        while True:
            ret = self.socket.recv(2048)

            ############# RESET TIMER!!! ##############

            if ret is None:
                continue

            header = ret[:12]

            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if self.seq == ack or ackflag != 0:
                break

        self.seq += 1

    def stop_and_wait_receiver(self):
        ret = self.socket.recv(2048)
        print(ret)

        if ret is not None:
            self.socket.sendto(
                self.create_packet(0, self.seq, 4, 0, b''), self.client
            )
        msg = ret[12:]
        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)

        if (self.seq == seq):
            print(msg)
            self.seq += 1
            return msg

        if self.parse_flags(flags)[2] != 0:
            self.socket.close()
            return 'fin'
