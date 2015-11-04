# -*- coding: utf-8 -*-

import argparse
import os
import sys
from select import select
import socket
import signal
import time
import logging
from logging import info, debug, warning, error
import hashlib
import hmac

from fyuneru.ipc.client import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.procmgr import ProcessManager
from fyuneru.util.debug import configLoggingModule
from fyuneru.ipc.url import IPCServerURL

ENCRYPTION_METHOD = 'aes-256-cfb'

##############################################################################

# ----------- parse arguments

parser = argparse.ArgumentParser()

parser.add_argument("--debug", action="store_true", default=False)
parser.add_argument("IPC_SERVER_URL", type=str)

args = parser.parse_args()

##############################################################################

configLoggingModule(args.debug)

##############################################################################

# use command line to initialize IPC client

ipc = InternalSocketClient(args.IPC_SERVER_URL)

queried = False

def queryFiller(packet):
    global ipc 
    packet.question = 'init'
    packet.arguments = {"name": ipc.name}
    return True

def infoReader(packet):
    global queried
    try:
        title = packet.title
        if title != 'init': return
        queried = {
            "user": (packet.uid, packet.gid),
            "config": packet.config,
            "key": packet.key,
            "mode": packet.mode,
        }
    except:
        pass
ipc.onInfo(infoReader)

info("Initializing shadowsocks proxy. Waiting for configuration.")
i = 0
while i < 5:
    ipc.doQuery(queryFiller)
    r = select([ipc], [], [], 1.0)[0]
    i += 1
    if len(r) < 1: continue
    ipc.receive()
    if queried: break

if not queried:
    error("Configuration timed out. Exit.")
    ipc.close()
    sys.exit(1)


##############################################################################

debug("Drop privilege to %s:%s" % queried["user"])
dropRoot(*queried["user"])

##############################################################################

# start shadowsocks process

procmgr = ProcessManager()

sharedsecret= hmac.HMAC(
    str(ipc.name + '-shadowsocks'),
    queried["key"],
    hashlib.sha256
).digest().encode('base64').strip()
proxyConfig = queried["config"]

forwardToPort = proxyConfig["server"]["forward-to"] # exit port at server

if 'c' == queried["mode"]: # CLIENT mode
    if proxyConfig["client"].has_key("proxy"):
        connectIP = proxyConfig["client"]["proxy"]["ip"]
        connectPort = proxyConfig["client"]["proxy"]["port"]
    else:
        connectIP = proxyConfig["server"]["ip"]
        connectPort = proxyConfig["server"]["port"]
    sscmd = [
        proxyConfig["client"]["bin"],                   # shadowsocks-libev
        '-U',                                           # UDP relay only
        '-L', "127.0.0.1:%d" % forwardToPort,           # destinating UDP addr
        '-k', sharedsecret,                             # key
        '-s', connectIP,                                # server host
        '-p', str(connectPort),                         # server port
        '-b', "127.0.0.1",                              # local addr
        '-l', str(proxyConfig["client"]["port"]),       # local port(entrance)
        '-m', ENCRYPTION_METHOD,                        # encryption method
    ]
elif 's' == queried['mode']: # SERVER mode
    sscmd = [
        proxyConfig["server"]["bin"],                   # shadowsocks-libev
        '-U',                                           # UDP relay only
        '-k', sharedsecret,                             # key
        '-s', proxyConfig["server"]["ip"],              # server host
        '-p', str(proxyConfig["server"]["port"]),       # server port
        '-m', ENCRYPTION_METHOD,                        # encryption method
    ]
else:
    sys.exit(127)

procmgr.new('shadowsocks', sscmd)
    

##############################################################################

proxySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if 's' == queried["mode"]:
    proxySocket.bind(('127.0.0.1', forwardToPort))
    proxyPeer = None                  # not knowing where to send data back
else:
    # send to local tunnel entrance
    proxyPeer = ('127.0.0.1', proxyConfig["client"]["port"])

##############################################################################

def doExit(signum, frame):
    global ipc, proxySocket, procmgr
    try:
        ipc.close()
    except:
        pass
    try:
        proxySocket.close()
    except:
        pass
    try:
        procmgr.killall()
    except:
        pass
    info("Exit now.")
    exit()
signal.signal(signal.SIGTERM, doExit)

##############################################################################

while True:
    try:
        ipc.heartbeat()

        selected = select([ipc, proxySocket], [], [], 1.0)
        if len(selected) < 1:
            continue
        readables = selected[0]

        for each in readables:
            if each == ipc:
                buf = ipc.receive()
                if None == buf: continue
                if None == proxyPeer: continue
                debug("Received %d bytes, sending to tunnel." % len(buf))
                proxySocket.sendto(buf, proxyPeer)
            
            if each == proxySocket:
                buf, sender = each.recvfrom(65536)
                proxyPeer = sender
                debug("Received %d bytes, sending back to core." % len(buf))
                ipc.send(buf)

        if ipc.broken: doExit(None, None)
    except KeyboardInterrupt:
        doExit(None, None)
