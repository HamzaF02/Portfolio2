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

        sync = self.create_packet(self.seq, 0, 8, 0, 0, '')

        start_time = time.time()
        self.socket.send(sync)
        ret = self.socket.recv(1024)
        end_time = time.time()

        if ret is None:
            print("ERROR. Synchronize acknowledgment not received")
            self.socket.close()
            sys.exit()

        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]
        syn, ackflag, fin = self.parse_flags(flags)
        if syn != 1 or ackflag != 1 or ack != self.seq:
            print("ERROR. Synchronize acknowledgment not received")
            self.socket.close()
            sys.exit()
        end_time = time.time()

        self.socket.timeout(end_time-start_time*4000)

        self.socket.send(self.create_packet(0, 1, 4, 0, 0, ''))
        self.seq += 1

    def bind(self):
        self.socket.bind((self.ip, self.port))

        sync = self.socket.recv(1024)
        header = sync[:12]

        seq, ack, flags, win = self.parse_header[header]
        syn, ackflag, fin = self.parse_flags(flags)

        if syn != 1:
            print("ERROR. Synchronize not received")
            self.socket.close()
            sys.exit()

        sync = self.create_packet(self.seq, 0, 12, 0, 0, '')

        start_time = time.time()
        self.socket.send(sync)
        ret = self.socket.recv(1024)
        end_time = time.time()

        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]
        syn, ackflag, fin = self.parse_flags(flags)

        if self.seq != ack or ackflag == 0:
            print("ERROR. Acknowledgement of Acknowledgement of Synchronize not received")
            self.socket.close()
            sys.exit()

    def close(self):
        fin = self.create_packet(self.seq, 0, 2, 0, 0, '')

        self.socket.send(fin)
        ret = self.socket.recv(1024)

        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]
        syn, ackflag, fin = self.parse_flags(flags)

        if self.seq != ack or ackflag == 0:
            print("ERROR. Acknowledgement of fin not received")
            self.socket.close()
            sys.exit()
        self.socket.close()

    def stop_and_wait_sender(self, data):
        self.socket.send(data)
        ret = self.socket.recv(1024)

        ############# RESET TIMER!!! ##############

        if ret is None:
            self.stop_and_wait_sender(data)
            return

        header = ret[:12]

        seq, ack, flags, win = self.parse_header[header]
        syn, ackflag, fin = self.parse_flags(flags)

        if self.seq != ack or ackflag == 0:
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

        if self.parse_flags(flags)[2] == 1:
            self.socket.close()
