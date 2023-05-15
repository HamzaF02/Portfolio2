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
    stop = False
    gbn = True

    if args.reliablemethod == 'gbn':
        gbn = True
    if args.reliablemethod == 'stop':
        stop = True
    if stop:
        while packet:
            clientSocket.stop_and_wait_sender(packet)
            packet = f.read(1460)
    if gbn:
        data = [b'', b'', b'']

        while packet:
            data.append(packet)
            packet = f.read(1460)
        clientSocket.GBN(data)

    clientSocket.close()

    # f = open(name, "rb")
    # f.read(1460)
    # print(f.read(1460))


def server():
    serverSocket = DRTP(args.ip, args.port)

    serverSocket.bind()
    stop = False
    gbn = True

    startInfo = serverSocket.stop_and_wait_receiver()
    g = open("new.jpg", "wb")

    if args.reliablemethod == 'gbn':
        gbn = True
    if args.reliablemethod == 'stop':
        stop = True
    if stop:
        meld = b''

        while True:
            m = serverSocket.stop_and_wait_receiver()

            if m == 'fin':
                break
            meld += m

    if gbn:
        meld = serverSocket.GBN_R()

    # print(meld)
    g.write(meld)


if args.client:
    client()
elif args.server:
    server()
