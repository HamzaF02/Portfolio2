from socket import *
import _thread as thread
import sys
import argparse

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
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    port = args.port
    ip = args.ip

    try:
        clientSocket.connect((ip, port))
    except:
        print("Failed to connect")
        sys.exit()

    name = args.filename
    clientSocket.send(name.encode())

    f = open(name, "rb")

    packet = f.read(1024)
    while packet:
        clientSocket.send(packet)
        packet = f.read(1024)

    clientSocket.send("end".encode())

    clientSocket.close()


def server():
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    port = args.port
    ip = args.ip

    try:
        serverSocket.bind((ip, port))
    except:
        print("ERROR: Binding failed")
        sys.exit()

    startInfo = serverSocket.recv(1024)

    meld = b''

    g = open("new_"+startInfo.decode(), "wb")
    while True:
        m = serverSocket.recv(1024)
        if m == b'end':
            break
        meld += m

    g.write(meld)

    serverSocket.close()


if args.client:
    client()
elif args.server:
    server()
