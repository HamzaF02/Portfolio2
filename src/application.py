# importing modules for system
from socket import *
import _thread as thread
import sys
import argparse
import time

# importing our DRTP program from another file to make it more universal
from DRTP import DRTP

# This is the file transfer application

# It has the arguments for both server and client side
parser = argparse.ArgumentParser()

# Chooses between server or client mode
parser.add_argument('-s', '--server', action='store_true',
                    help='Runs program in server mode')
parser.add_argument('-c', '--client', action='store_true',
                    help='Runs program in client mode')

# Determine ip and port for socket binding and connection
parser.add_argument('-i', '--ip', type=str, default='127.0.0.1',
                    help='Selects the ip address of the server')
parser.add_argument('-p', '--port', type=int, default=8088,
                    help='Allows you to select the port')

# Determine file to be transfered, this is only for client
parser.add_argument('-f', '--filename', type=str,
                    help='The file to transfer')

# Choose between three reliable methods, stop_and_wait, Go-Back-N and Selective-Repeat
parser.add_argument('-r', '--reliablemethod', type=str,
                    help='Starts the reliable method chosen', choices=['stop', 'gbn', 'sr'])

# Test code in case of artificial packet loss or loss of acknowledment to test reliability
parser.add_argument('-t', '--testcase', type=str,
                    help='Starts the test case chosen', choices=['loss', 'skip_ack'])

# Parsing the arguments
args = parser.parse_args()


def client():
    # Opens a DRTP connection socket with given testcases
    clientSocket = DRTP(args.ip, args.port, args.testcase)

    # Connects to the server and syncs with server
    clientSocket.connect()

    # Gets the filename and sends it through to the server for it to open it's file
    name = args.filename
    clientSocket.socket.send(name.encode())

    # Opening the file in read bytes mode, since not all files are written inn string
    f = open(name, "rb")

    # Reading the file in packets of 1460 and adding it to list
    packet = f.read(1460)
    data = []

    # Total data to calculate throughput
    throughput = 0

    # Adding to list until no more data and adds data amount into throughput
    while packet:
        data.append(packet)
        packet = f.read(1460)
        throughput += len(packet)

    # Starts the timer for calculating throughput
    start_time = time.time()

    # Chooses method to run based on input argument
    if args.reliablemethod == 'stop':
        clientSocket.stop_and_wait_sender(data)

    elif args.reliablemethod == 'gbn':
        clientSocket.GBN(data)

    elif args.reliablemethod == 'sr':
        clientSocket.SR(data)

    # Closes the system smoothly
    clientSocket.close()

    # Stops timer
    end_time = time.time()

    # Formating amount of data into Mbps for throughput and prints out the value
    throughput = 8*throughput/(end_time-start_time)
    throughput = throughput/1_000_000
    print("Throughput: ", throughput, "Mbps")


def server():
    # Opens a DRTP connection socket with given testcases
    serverSocket = DRTP(args.ip, args.port, args.testcase)

    # Binds to the address (ip,port) and syncs with client
    serverSocket.bind()

    # Variable for writing to file
    file = b''

    # A packet to get the file name and then opens a new version of it to write on in byte mode
    startInfo = serverSocket.socket.recv(1024)
    g = open("new"+startInfo.decode(), "wb")

    # Gets content from one of the methods
    if args.reliablemethod == 'stop':
        file = serverSocket.stop_and_wait_receiver()

    elif args.reliablemethod == 'gbn':
        file = serverSocket.GBN_R()

    elif args.reliablemethod == 'sr':
        file = serverSocket.SR_R()

    # writes the content to file
    g.write(file)


if args.client and not args.server:
    client()
elif args.server and not args.client:
    server()
