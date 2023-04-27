from socket import *
import _thread as thread
import sys
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--server', action='store_true',
                    help='Runs program in server mode')
parser.add_argument('-c', '--client', action='store_true',
                    help='Runs program in client mode')

args = parser.parse_args()


def client():
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    port = 8080
    ip = "127.0.0.1"
    try:
        clientSocket.connect((ip, port))
    except:
        print("Failed to connect")
        sys.exit()
    name = input("Filename: ")
    clientSocket.send(name.encode())

    f = open(name, "rb").read()

    for i in f:
        clientSocket.send(i.encode())


def server():
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    port = 8080
    # ip = "127.0.0.1"

    try:
        serverSocket.bind(('', port))
    except:
        print("ERROR: Binding failed")
        sys.exit()

    # serverSocket.listen(1)

    startInfo, clientAddress = serverSocket.recvfrom(1024)

    g = open("new"+startInfo.decode(), "wb")
    while True:
        m, clientAddress = serverSocket.recvfrom(1024)
        m = m.decode()

        if not m:
            break
        else:
            g.write(m)


if args.client:
    client()
elif args.server:
    server()
