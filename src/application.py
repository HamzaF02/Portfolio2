from socket import *
import _thread as thread
import sys
import time
import argparse
import ipaddress
import re

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--server', action='store_true',
                    help='Runs program in server mode')
parser.add_argument('-c', '--client', action='store_true',
                    help='Runs program in client mode')

args = parser.parse_args()


def client():
    a


def server():
    a


if args.client:
    client()
elif args.server:
    server()
