from socket import *
import _thread as thread
import sys
import argparse

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
    clientSocket = DRTP(args.ip, args.port)

    clientSocket.connect()

    name = args.filename
    print(name)
    clientSocket.stop_and_wait_sender(name.encode())

    f = open(name, "rb")

    packet = f.read(1460)
    while packet:
        print(packet)
        clientSocket.stop_and_wait_sender(packet)
        packet = f.read(1460)
    clientSocket.close()


def server():
    serverSocket = DRTP(args.ip, args.port)

    serverSocket.bind()

    startInfo = serverSocket.stop_and_wait_receiver()
    # print(startInfo)

    meld = b''

    g = open("new.jpg", "wb")
    while True:
        m = serverSocket.stop_and_wait_receiver()

        if m == 'fin':
            break
        meld += m
    print(meld)
    g.write(meld)


if args.client:
    client()
elif args.server:
    server()
