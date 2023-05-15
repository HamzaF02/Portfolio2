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

            # waits for a message to receive
            while True:
                try:
                    ret = self.socket.recv(1472)
                except timeout:
                    continue
                break

            if test:
                test = False
                continue

            # Gets the information sendt by client
            msg = ret[12:]

            # Gets header from packet and parses it into usable information
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            # Sends a acknowledment packet
            self.socket.sendto(
                self.create_packet(0, seq, 4, self.win, b''), self.client
            )

            # If it is a finnish packet it closese the socket and returns the file
            if fin != 0:
                self.socket.close()
                break

            # if its the correct sequence and not a duplicate, it will write it to file and increase its counter
            elif (self.seq == seq):
                self.seq += 1
                file += msg

        return file

    # Go-Back-N is a reliable method of sending multiple packets without instantly waiting for acknowledgement
    # It works by sending multiple packets and then waits for acknoledments from server before sending more
    def GBN(self, data):
        # Windows for sliding windows, can only send so much before waiting for acknowledgment
        window = []
        # Starts with three empty variables to make til line up with sequence
        # (Could be done with loop for switching between modes)
        data = [b'', b'', b'']+data

        # Loss test
        test = False
        if self.testcase == "loss":
            test = True

        # Fills up window with sequences to send until there is either no more spots in window or no more packets
        while len(window) < self.win:
            if len(data) <= self.seq:
                break
            window.append(self.seq)
            self.seq += 1

        # Will send and receive in correct order until there is no more data
        while True:

            # Creates and sends every packet in window, misses one incase of loss test
            for i in range(0, len(window)):
                p = self.create_packet(
                    window[i], 0, 0, self.win, data[window[i]])

                if test == True:
                    test = False
                else:
                    self.socket.send(p)

            # As long as there are values in window it breaks this will continue
            while len(window) > 0:
                # Tries to receive acknolegdements, if not it will send everthing in the window again
                try:
                    ret = self.socket.recv(1472)

                except timeout:
                    break

                # Gets header from packet and parses it into usable information
                header = ret[:12]
                seq, ack, flags, win = self.parse_header(header)

                # If the recieved ack packet is not for the first packet, it will send everthing in window again
                if (ack > window[0]):
                    break
                else:
                    # if correct ack packets arrives, it pops it out of window and adds the next one in the list
                    window.pop(0)

                    if len(data) <= self.seq:
                        continue

                    # Creates and sends the next packet
                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[self.seq])
                    self.socket.send(p)

                    # Adds it to the window list
                    window.append(self.seq)

                    # seqeunce increased, packet succecfully obtained
                    self.seq += 1

            # if the procces is complete, close loop
            if len(data) <= self.seq and len(window) == 0:
                break

    # Go-Back-N is a reliable method of sending multiple packets without instantly waiting for acknowledgement
    # Server side works by receiving packets in order and ignoring anything else
    def GBN_R(self):

        # Storage of the information to be returned
        file = b''

        # A test to test what skipping and ack does, and if server sends dup
        test = False
        if self.testcase == "skip_ack":
            test = True

        while True:

            # Waits for a message to receive
            while True:
                try:
                    ret = self.socket.recv(1472)
                except timeout:
                    continue
                break

            if test:
                test = False
                continue

            # Gets the information sendt by client
            msg = ret[12:]

            # Gets header from packet and parses it into usable information
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            # Only send ack to duplicates or the correct packet
            if seq <= self.seq:
                self.socket.sendto(
                    self.create_packet(0, seq, 4, self.win, b''), self.client)

            # If it is a finish packet it closes the socket and returns the file
            if fin != 0:

                self.socket.close()
                break
            # If it is the correct packet, and add it file
            elif (self.seq == seq):
                self.seq += 1
                file += msg

        return file

    def SR(self, data):

        # Windows for sliding windows, can only send so much before waiting for acknowledgment
        window = []
        # Starts with three empty variables to make til line up with sequence
        # (Could be done with loop for switching between modes)
        data = [b'', b'', b'']+data

        # Loss test
        test = False
        if self.testcase == "loss":
            test = True

        while True:

            # If window is not full, it fills it untill there are no more packets/sequence numbers
            while len(window) < self.win:
                if len(data) <= self.seq:
                    break
                window.append(self.seq)
                self.seq += 1

            # Then procceeds to send every packet in window, ignores the first if test asks for it
            for i in range(len(window)):
                p = self.create_packet(
                    window[i], 0, 0, self.win, data[window[i]])
                if test:
                    test = False
                else:
                    self.socket.send(p)

            # While there are values in window
            while len(window) > 0:
                # Tries to receive acknolegdements, if not it will send everthing in the window again
                try:
                    ret = self.socket.recv(1472)

                except timeout:
                    break

                # Gets header from packet and parses it into usable information
                header = ret[:12]
                seq, ack, flags, win = self.parse_header(header)

                # If correct ack is received
                if (ack == window[0]):
                    # pops out the first
                    window.pop(0)

                    # If no more packets are present it leaves it
                    if len(data) <= self.seq:
                        continue

                    # Creates and sends packet
                    p = self.create_packet(
                        self.seq, 0, 0, self.win, data[self.seq])
                    self.socket.send(p)

                    # Adds sequence number to window and increases the number
                    window.append(self.seq)
                    self.seq += 1

                # If its the wrong ack packet
                elif ack > window[0]:

                    # Gets posisition of packet that ack was meant for
                    index = window.index(ack)

                    # The packets that needs to resent
                    buffer = window[0:index]

                    # makes the rest of window
                    if len(window) < index+1:
                        window = []
                    else:
                        window = window[index+1:]

                    # A kind of stop and wait will occur untill buffer list has been emptied
                    while len(buffer) > 0:
                        # Resends the packets
                        for i in range(len(buffer)):
                            p = self.create_packet(
                                buffer[i], 0, 0, self.win, data[buffer[i]])

                            self.socket.send(p)

                        while True:
                            # Tries to receives packets, if it wont arrive we resend buffer packets
                            try:
                                ret = self.socket.recv(1472)
                            except timeout:
                                break

                            # Gets header from packet and parses it into usable information
                            header = ret[:12]
                            seq, ack, flags, win = self.parse_header(header)

                            # If ack is for a packet in buffer, it removes it
                            try:
                                buffer.remove(ack)
                            except:
                                # if it is a packet in window, it removes it
                                if window.count(ack) > 0:
                                    window.remove(ack)

            # if the procces is complete, close loop
            if len(data) <= self.seq and len(window) == 0:
                break

    def SR_R(self):
        # Lists for reordering and storage of buffered packets
        window = []
        windowseq = []

        # Storage of the information to be returned
        file = b''

        # A test to test what skipping and ack does, and if server sends dup
        test = False
        if self.testcase == "skip_ack":
            test = True

        while True:

            # Waits for a message to receive
            while True:
                try:
                    ret = self.socket.recv(1472)
                except timeout:
                    continue
                break

            if test:
                test = False
                continue

            # Gets the information sendt by client
            msg = ret[12:]

            # Gets header from packet and parses it into usable information
            header = ret[:12]
            seq, ack, flags, win = self.parse_header(header)
            syn, ackflag, fin = self.parse_flags(flags)

            if test:
                test = False
                continue

            # Sends and ack packet to client no matter what packet it received
            self.socket.sendto(
                self.create_packet(0, seq, 4, self.win, b''), self.client)

            # If it is the fin packet, it closes the packet and return file
            if fin != 0:
                self.socket.close()
                break

            # If the correct packet arrives, it handles it like noramlly
            if seq == self.seq:
                file += msg
                self.seq += 1

            # If it is the wrong packet, it will be added to window in the correct posistion
            elif seq > self.seq:

                # Adding sequence to seqlist, and then using sorting and indexing to find the correct posistion for packet
                windowseq.append(seq)
                windowseq.sort()
                i = windowseq.index(seq)

                # Placing information into the list for later use
                window = window[0:i]+[msg]+window[i:]

            # Goes through the lists to see if time to leave buffer by matching it to servers sequence counter
            while len(windowseq) > 0:
                if windowseq[0] != self.seq:
                    break
                file += window.pop(0)
                windowseq.pop(0)
                self.seq += 1

        return file
