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
    port = 8088
    ip = "127.0.0.1"
    try:
        clientSocket.connect((ip, port))
    except:
        print("Failed to connect")
        sys.exit()
    name = input("Filename: ")
    clientSocket.send(name.encode())

    f = open(name, "rb").read()
    f = str(f).split()
    print(f[0].encode())
    for i in range(0, len(f)):
        clientSocket.send(bytes(f[i]))

    # clientSocket.send("done".encode())

    clientSocket.close()


def server():
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    port = 8088
    # ip = "127.0.0.1"

    try:
        serverSocket.bind(('127.0.0.1', port))
    except:
        print("ERROR: Binding failed")
        sys.exit()

    # serverSocket.listen(1)

    startInfo = serverSocket.recv(1024)

    g = open("new_"+startInfo.decode(), "wb")
    while True:
        m = serverSocket.recv(4096)
        g.write(m)
        # m = m.decode()

        # if m[-4:] == "done":
        #     # print(m[:-4])
        #     g.write(m[:-4].encode())
        #     break
        # else:
        #     # print(m)
        #     g.write(m.encode())

    serverSocket.close()


if args.client:
    client()
elif args.server:
    server()
