from struct import *
from socket import *
import sys
import time


class DRTP:
    def __init__(self, ip, port, test):
        self.ip = ip
        self.port = port
        self.header_format = '!IIHH'
        self.seq = 1
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.timeout = 0.5
        self.testcase = test
        self.througput = 0

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

        self.socket.send(sync)
        try:
            ret = self.socket.recv(1472)
        except:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        header = ret[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)
        if syn == 0 or ackflag == 0 or seq != self.seq:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        self.win = win
        try:

            self.socket.send(self.create_packet(
                0, seq, 4, self.win, b''))
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
        self.win = 5

        header = sync[:12]

        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        if syn == 0:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        sync = self.create_packet(self.seq, 0, 12, self.win, b'')

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
            fin = self.create_packet(self.seq, 0, 2, self.win, b'')

            try:
                self.socket.send(fin)
            except:
                break

            try:
                ret = self.socket.recv(1472)

            except:
                continue

            header = ret[:12]

            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if self.seq == ack and ackflag != 0:
                break

        self.socket.close()

    def stop_and_wait_sender(self, data):

        test = False
        if self.testcase == "loss":
            test = True
        for i in range(len(data)):
            while True:
                if test:
                    test = False
                else:
                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[i])
                    self.througput += len(p)

                    self.socket.send(p)

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
        return self.througput

    def stop_and_wait_receiver(self):
        file = b''
        test = False
        if self.testcase == "skip_ack":
            test = True

        while True:

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

            if test:
                test = False
                continue

            self.socket.sendto(
                self.create_packet(0, seq, 4, self.win, b''), self.client
            )

            if fin != 0:
                self.socket.close()
                break
            elif (self.seq == seq):
                self.seq += 1
                file += msg

        return file

    def GBN(self, data):
        window = []
        data = [b'', b'', b'']+data
        test = False
        if self.testcase == "loss":
            test = True

        while len(window) < self.win:
            if len(data) <= self.seq:
                break

            window.append(self.seq)

            self.seq += 1

        while True:

            for i in range(0, len(window)):
                p = self.create_packet(
                    window[i], 0, 0, self.win, data[window[i]])
                self.througput += len(p)

                if test == True:
                    test = False
                else:
                    self.socket.send(p)

            while len(window) > 0:
                try:
                    ret = self.socket.recv(1472)

                except:
                    break

                seq, ack, flags, win = self.parse_header(ret[:12])

                if (ack > window[0]):
                    break
                else:
                    window.pop(0)

                    if len(data) <= self.seq:
                        continue

                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[self.seq])
                    self.througput += len(p)

                    self.socket.send(p)

                    window.append(self.seq)
                    self.seq += 1

            if len(data) <= self.seq and len(window) == 0:
                break
        return self.througput

    def GBN_R(self):
        file = b''
        done = True
        test = False
        if self.testcase == "skip_ack":
            test = True

        while True:

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
            if test:
                test = False
                continue

            if fin != 0:
                self.socket.sendto(
                    self.create_packet(0, seq, 4, self.win, b''), self.client)
                self.socket.close()
                break

            elif (self.seq == seq):
                self.socket.sendto(
                    self.create_packet(0, seq, 4, self.win, b''), self.client)
                self.seq += 1
                file += msg

        return file

    def SR(self, data):
        window = []
        data = [b'', b'', b'']+data

        test = False

        if self.testcase == "loss":
            test = True

        while True:

            while len(window) < self.win:
                if len(data) <= self.seq:
                    break
                window.append(self.seq)

                self.seq += 1

            for i in range(len(window)):
                p = self.create_packet(
                    window[i], 0, 0, self.win, data[window[i]])

                self.througput += len(p)

                if test:
                    test = False
                else:
                    self.socket.send(p)

            while len(window) > 0:
                try:
                    ret = self.socket.recv(1472)
                except:
                    break

                seq, ack, flags, win = self.parse_header(ret[:12])
                print(ack)

                if (ack == window[0]):
                    window.pop(0)

                    if len(data) <= self.seq:
                        continue

                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[self.seq])
                    self.througput += len(p)

                    self.socket.send(p)

                    window.append(self.seq)
                    self.seq += 1

                else:

                    index = window.index(ack)

                    buffer = window[0:index]

                    if len(window) < index+1:
                        window = []
                    else:
                        window = window[index+1:]

                    while len(buffer) > 0:
                        for i in range(len(buffer)):
                            p = self.create_packet(
                                buffer[i], 0, 0, self.win, data[buffer[i]])

                            self.socket.send(p)

                        while True:
                            try:
                                ret = self.socket.recv(1472)
                            except:
                                break

                            seq, ack, flags, win = self.parse_header(ret[:12])
                            print(ack)

                            try:
                                buffer.remove(ack)
                            except:
                                if window.count(ack) > 0:
                                    window.remove(ack)

            if len(data) <= self.seq and len(window) == 0:
                break
        return self.througput

    def SR_R(self):
        file = b''
        window = []
        windowseq = []
        test = False

        if self.testcase == "skip_ack":
            test = True

        while True:

            while True:
                try:
                    ret = self.socket.recv(1472)
                except:
                    continue

                break

            msg = ret[12:]
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            print(seq)

            if test:
                test = False
                continue

            self.socket.sendto(
                self.create_packet(0, seq, 4, self.win, b''), self.client)

            syn, ackflag, fin = self.parse_flags(flags)

            if fin != 0:
                self.socket.close()
                break

            if seq == self.seq:
                file += msg
                self.seq += 1
            elif seq > self.seq:

                windowseq.append(seq)
                windowseq.sort()
                i = windowseq.index(seq)

                window = window[0:i]+[msg]+window[i:]

            while len(windowseq) > 0:
                if windowseq[0] != self.seq:
                    break
                file += window.pop(0)
                windowseq.pop(0)
                self.seq += 1

        return file
