
# -*- coding: utf-8 -*-

"""
Internal Fyuneru Socket for Proxy Processes

A fyuneru socket basing on UDP socket is defined. It is always a listening UDP
socket on a port in local addr, which does automatic handshake with given
internal magic word, and provides additionally abilities like encryption
underlays, traffic statistics, etc.
"""

from logging import debug, info, warning, error, exception
from time import time
from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

IPCPort = 64089

##############################################################################

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
