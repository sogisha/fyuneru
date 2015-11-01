# -*- coding: utf-8 -*-

"""
Internal Fyuneru Socket for Proxy Processes

A fyuneru socket basing on UDP socket is defined. It is always a listening UDP
socket on a port in local addr, which does automatic handshake with given
internal magic word, and provides additionally abilities like encryption
underlays, traffic statistics, etc.
"""

import os
import sys
from logging import debug, info, warning, error, exception
from time import time
from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM
import random
from ..util.crypto import Crypto

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

IPCPort = 64089

##############################################################################

class InternalSocketServer:

    __sockpath = None
    __sock = None

    peers = {}

    sendtiming = 0
    recvtiming = 0

    def __init__(self, key):
        self.__crypto = Crypto(key)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind(("127.0.0.1", IPCPort))

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def __registerPeer(self, addrTuple):
        self.peers[addrTuple] = time() 

    def close(self):
        # close socket
        debug("Internal socket shutting down...")
        try:
            self.__sock.close()
        except Exception,e:
            error("Error closing socket: %s" % e)

    def clean(self):
        # reserved for doing clean up jobs relating to the peer delays
        removeList = []
        now = time()
        for each in self.peers:
            if not self.peers[each]:
                removeList.append(each)
            elif now - self.peers[each] > 5:
                removeList.append(each)
        for each in removeList:
            del self.peers[each]

    def receive(self):
        buf, sender = self.__sock.recvfrom(65536)

        if buf.strip() == UDPCONNECTOR_WORD:
            # connection word received, answer
            self.__registerPeer(sender)
            self.__sock.sendto(UDPCONNECTOR_WORD, sender)
            return None

        decryption = self.__crypto.decrypt(buf)
        if not decryption: return None

        if len(decryption) < 8: return None
        header = decryption[:8]
        timestamp = unpack('<d', header)[0]
        buf = decryption[8:]

        self.recvtiming = max(self.recvtiming, timestamp)
        self.__registerPeer(sender)
        return buf 

    def send(self, buf):
        # choose a peer randomly
        possiblePeers = [i for i in self.peers if self.peers[i]]
        if len(possiblePeers) < 1: return
        peer = possiblePeers[random.randrange(0, len(possiblePeers))]
        # send to this peer
        self.sendtiming = time()
        header = pack('<d', self.sendtiming)
        encryption = self.__crypto.encrypt(header + buf)
        try:
            # reply using last recorded peer
            self.__sock.sendto(encryption, peer)
        except Exception,e:
            error(e) # for debug
            self.peers[peer] = False # this peer may not work


class InternalSocketClient:

    __sock = None
    __peer = ("127.0.0.1", IPCPort) 
    
    connected = False
    broken = False

    __lastbeatSent = 0
    __lastbeatRecv = 0

    def __init__(self):
        self.__sock = socket(AF_INET, SOCK_DGRAM)

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def __registerLastBeatSent(self):
        self.__lastbeatSent = time()

    def __registerLastBeatRecv(self):
        self.__lastbeatRecv = time()
        self.connected = True
        self.broken = False

    def close(self):
        debug("IPC socket shutting down...")
        try:
            self.__sock.close()
        except Exception,e:
            error("Error closing socket: %s" % e)

    def heartbeat(self):
        tdiffSent = time() - self.__lastbeatSent
        tdiffRecv = time() - self.__lastbeatRecv
        if not self.connected or tdiffSent > 2:
            try:
                self.__registerLastBeatSent()
                self.__sock.sendto(UDPCONNECTOR_WORD, self.__peer)
                if not self.connected: debug("IPC heartbeat sent to server.")
            except Exception,e:
                exception(e)
                error("Heartbeat of IPC connection at client failed.")
                self.connected = False
                self.broken = True
        if self.connected and tdiffRecv > 5:
            warning("Stale IPC connection at client detected.")
            self.connected = False
            self.broken = True

    def receive(self):
        buf, sender = self.__sock.recvfrom(65536)
        if sender != self.__peer: return None
        if buf.strip() == UDPCONNECTOR_WORD:
            # connection word received, answer
            if self.connected == False: debug("IPC client connected.")
            self.__registerLastBeatRecv()
            return None
        return buf 

    def send(self, buf):
        if not self.connected: return
        try:
            # reply using last recorded peer
            self.__sock.sendto(buf, self.__peer)
        except Exception,e:
            exception(e)
            error("Failed sending buffer to IPC server.")
            self.connected = False # this peer may not work
            self.broken = True
