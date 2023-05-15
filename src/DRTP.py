# importing modules for systems
from struct import *
from socket import *
import sys
import time

# A system for adding reliability to udp connections


class DRTP:

    # Defining starting attributes
    def __init__(self, ip, port, test):
        # ip and port for connecting or binding
        self.ip = ip
        self.port = port

        # Format for packet headers
        self.header_format = '!IIHH'

        # Starting sequence for differentiating packets
        self.seq = 1

        # Creating a socket across udp
        self.socket = socket(AF_INET, SOCK_DGRAM)

        # A socket timeout time
        self.timeout = 0.5

        # Possible testcase incidents
        self.testcase = test

    # Packet creating funciton that formats informaiton into packets for sending
    # Inputs are given DRTP format
    def create_packet(self, seq, ack, flags, win, data):
        header = pack(self.header_format, seq, ack, flags, win)
        packet = header + data
        return packet

    # Unpacks the header back into the same kind of inputs as create_packets
    def parse_header(self, header):
        header_from_msg = unpack(self.header_format, header)
        return header_from_msg

    # makes a bit formatet flag system into variables
    def parse_flags(self, flags):
        syn = flags & (1 << 3)
        ack = flags & (1 << 2)
        fin = flags & (1 << 1)
        return syn, ack, fin

    # Connects the client to server and syncs
    def connect(self):
        # Connects to server so that server address is not constantly needed
        self.socket.connect((self.ip, self.port))

        # Creating a syncronizing packet with a sync flag on
        sync = self.create_packet(self.seq, 0, 8, 0, b'')

        # Setting a timeout for how long it will wait for recv before it stops
        self.socket.settimeout(0.5)

        # Send the sync packet
        self.socket.send(sync)

        # Waits for sync ack returning packet, if this fails a stable connection is not secured and ends the code
        try:
            ret = self.socket.recv(1472)
        except:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        # Gets the header from the packet by reading the first 12 bytes
        header = ret[:12]

        # Sends the header through parsing to make it understandable information
        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        # if it is not sync ack that was expected we end the system as it was a connection failure
        if syn == 0 or ackflag == 0 or seq != self.seq:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        # Retrives the window size for SR and GBN from the server
        self.win = win

        # Tries to send back a acknowledgement of sync acknowledment
        # Using Try in case of server closing during sync
        try:
            # sends a acknowledment packet, with ack flag on
            self.socket.send(self.create_packet(
                0, seq, 4, self.win, b''))
        except:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        # Increasing the sequence number since first packet has been send and acknowledegde
        self.seq += 1

    # Binds the server to an address and makes a connection with a client

    def bind(self):
        # tries to bind to address
        try:
            self.socket.bind((self.ip, self.port))
        except:
            sys.exit()

        # Waits for a possible client to send a sync message

        sync, self.client = self.socket.recvfrom(1472)

        # Sets a timeout now that a client has been determined
        self.socket.settimeout(0.5)

        # The servers window size
        self.win = 5

        # Gets header from packet and parses it into usable information
        header = sync[:12]
        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        # if it is not the expectet sync message it will close as something else is trying to connect
        if syn == 0:
            print("ERROR. Synchronize failed")
            self.socket.close()
            sys.exit()

        # Creates and tries to sends a synchronize acknowledge message back to the client with both sync and ack flag on, giving 12
        sync = self.create_packet(self.seq, 0, 12, self.win, b'')
        try:
            self.socket.sendto(sync, self.client)
        except:
            self.socket.close()
            print("ERROR. Synchronize failed")
            sys.exit()

        # Waits for clients acknowledgement of sync ack message
        ret = b''
        try:
            ret = self.socket.recv(1472)
        except:
            self.socket.close()
            print("ERROR. Synchronize failed")
            sys.exit()

        # Gets header from packet and parses it into usable information
        header = ret[:12]
        seq, ack, flags, win = self.parse_header(header)
        syn, ackflag, fin = self.parse_flags(flags)

        # if it is not the acknowledgment it was expecting, something went wrong and it needs to be closed
        if self.seq != ack or ackflag == 0:
            self.socket.close()
            print("ERROR. Synchronize failed")

        # Increasing the sequence number since first packet has been send and acknowledegde
        self.seq += 1

    # A function for client to send and wait for closure

    def close(self):
        # A while loops because it wont stop until a proper closure is acheived
        while True:

            # Creates a finish packet with the fin flag
            fin = self.create_packet(self.seq, 0, 2, self.win, b'')

            # Sends the finish packet with a try-except incase the socket is disconnected
            try:
                self.socket.send(fin)
            except:
                break

            # Tries to recieve the acknowledgement of finish, if timeout happends it will try again incase the packet was lost
            try:
                ret = self.socket.recv(1472)
            except timeout:
                continue

            # Gets header from packet and parses it into usable information
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            # If everything goes correct it will leaver the loop and close the socket
            if self.seq == ack and ackflag != 0:
                break

        self.socket.close()

    # Stop and wait is one of the reliable method and it takes in a list of data for the packets
    # It works by sending and then waiting for an acknoledment from server
    def stop_and_wait_sender(self, data):
        # If loss test is gonna occur, where does not send the first packet to check retransmission
        test = False
        if self.testcase == "loss":
            test = True

        # Stop and wait will be preformed on each packet, so a loop through list is utiliezd
        for i in range(len(data)):
            # Not stoppping until proper precedure is complete
            while True:

                # Utføring av loss test
                if test:
                    test = False
                else:
                    # Making a packet with data and sends it
                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[i])

                    self.socket.send(p)

                # Tries to recieve the acknowledge, if not it got back to the top and sends it again
                try:
                    ret = self.socket.recv(1472)
                except timeout:
                    continue

                # Gets header from packet and parses it into usable information
                header = ret[:12]
                seq, ack, flags, win = self.parse_header(header)
                syn, ackflag, fin = self.parse_flags(flags)

                # If correct ack packet it will go on to the next
                if self.seq == ack or ackflag != 0:
                    break

            # A packet has succesfully been sent and sequence is increased
            self.seq += 1

    # Stop and wait is one of the reliable method and it will return the information given
    # It works by wating for packet and sending an acknowledgement back
    def stop_and_wait_receiver(self):
        # Storage of the information to be returned
        file = b''

        # A test to test what skipping and ack does, and if server sends dup
        test = False
        if self.testcase == "skip_ack":
            test = True

        while True:

            waits for s
            while True:
                try:
                    ret = self.socket.recv(1472)
                except timeout:
                    continue
                brea

            if test:
                test = False
                continue

            # Gets the information sendt by client
            msg = ret[12:]

            # Gets header from packet and parses it into usable information
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

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

                    self.socket.send(p)

                    window.append(self.seq)
                    self.seq += 1

            if len(data) <= self.seq and len(window) == 0:
                break

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

                if (ack == window[0]):
                    window.pop(0)

                    if len(data) <= self.seq:
                        continue

                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[self.seq])

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

                            try:
                                buffer.remove(ack)
                            except:
                                if window.count(ack) > 0:
                                    window.remove(ack)

            if len(data) <= self.seq and len(window) == 0:
                break

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
