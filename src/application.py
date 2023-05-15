from socket import *
import _thread as thread
import sys
import argparse
import time

from DRTP import DRTP

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--server', action='store_true',
                    help='Runs program in server mode')
parser.add_argument('-c', '--client', action='store_true',
                    help='Runs program in client mode')
parser.add_argument('-i', '--ip', type=str, default='127.0.0.1',
                    help='Selects the ip address of the server')
parser.add_argument('-p', '--port', type=int, default=8088,
                    help='Allows you to select the port')
parser.add_argument('-f', '--filename', type=str,
                    help='The file to transfer')
parser.add_argument('-r', '--reliablemethod', type=str,
                    help='Starts the reliable method chosen')
parser.add_argument('-t', '--testcase', type=str,
                    help='Starts the test case chosen')


args = parser.parse_args()


def client():
    clientSocket = DRTP(args.ip, args.port, args.testcase)

    clientSocket.connect()

    name = args.filename
    clientSocket.socket.send(name.encode())

    f = open(name, "rb")

    packet = f.read(1460)
    stop = False
    gbn = False
    sr = True
    data = []
    throughput = 0

    while packet:
        data.append(packet)
        packet = f.read(1460)
        throughput += len(packet)

    start_time = time.time()
    if args.reliablemethod == 'stop':
        throughput = clientSocket.stop_and_wait_sender(data)

    elif args.reliablemethod == 'gbn':
        throughput = clientSocket.GBN(data)
    elif args.reliablemethod == 'sr':
        throughput = clientSocket.SR(data)

    clientSocket.close()
    end_time = time.time()

    throughput = 8*throughput/(end_time-start_time)
    throughput = int(throughput/1_000_000)

    print("Throughput: ", throughput, "Mbps")


def server():
    serverSocket = DRTP(args.ip, args.port, args.testcase)

    serverSocket.bind()
    stop = False
    gbn = False
    sr = True
    file = b''

    startInfo = serverSocket.socket.recv(1024)
    g = open("new"+startInfo.decode(), "wb")

    if args.reliablemethod == 'stop':
        file = serverSocket.stop_and_wait_receiver()

    elif args.reliablemethod == 'gbn':
        file = serverSocket.GBN_R()
    elif args.reliablemethod == 'sr':
        file = serverSocket.SR_R()

    g.write(file)


if args.client:
    client()
elif args.server:
    server()
