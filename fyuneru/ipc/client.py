
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

from fyuneru.util.crypto import Authenticator
from __protocol import *
from .url import IPCServerURL

##############################################################################

class InternalSocketClient:

    __sock = None
    __name = None
    __peer = (None, None) 
    
    connected = False
    broken = False

    __lastbeatSent = 0
    __lastbeatRecv = 0

    __infoHandler = None

    def __init__(self, serverURL):
        server = IPCServerURL(serverURL)

        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__authenticator = Authenticator(server.key)
        self.__peer = (server.host, server.port)
        self.name = server.user

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    # ---------- heartbeat related

    def __registerLastBeatSent(self):
        self.__lastbeatSent = time()

    def __registerLastBeatRecv(self):
        self.__lastbeatRecv = time()
        self.connected = True
        self.broken = False

    # ---------- internal mechanism dealing with outbound/inbound data

    def __sendPacket(self, packet):
        """Send a packet class to a destination using local socket."""
        s = self.__authenticator.sign(str(packet))
        self.__sock.sendto(s, self.__peer)

    def __recvBuffer(self, buf, sender):
        """Receive a buffer, unpack into packet, and dispatch it to different
        handlers. Returns buffer when unpacked is a DataPacket. Otherwise
        None."""
        # filter out traffic that's not originating from what we thought
        if sender != self.__peer: return None
        # See if is a data packet, which is special.
        buf = self.__authenticator.verify(buf)
        if not buf: return None # signature check failed
        packet = loadBufferToPacket(buf)
        if not packet: return None
        if isinstance(packet, DataPacket): return packet.buffer

        # If not, call different handlers to handle this.
        if isinstance(packet, HeartbeatPacket):
            self.__handleHeartbeatPacket(packet)
            return None
        if isinstance(packet, InfoPacket):
            self.__handleInfoPacket(packet)
            return None

    # ---------- inner handlers for different packets

    def __handleHeartbeatPacket(self, packet):
        # heart beat reply received, answer
        if self.connected == False: debug("IPC client connected.")
        self.__registerLastBeatRecv()

    def __handleInfoPacket(self, packet):
        if self.__infoHandler: self.__infoHandler(packet)

    # ---------- public functions

    def doQuery(self, fillerFunc):
        packet = QueryPacket()
        s = fillerFunc(packet)
        if s:
            debug("Sent a query packet.")
            self.__sendPacket(packet)

    def onInfo(self, handler):
        self.__infoHandler = handler

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
                self.__sendPacket(HeartbeatPacket())
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
        buf = self.__recvBuffer(buf, sender) # pre handling this buffer

        if not buf: return None # digested within other mechanism. exit.
        return buf 

    def send(self, buf):
        if not self.connected: return
        try:
            packet = DataPacket()
            packet.buffer = buf
            self.__sendPacket(packet)
        except Exception,e:
            exception(e)
            error("Failed sending buffer to IPC server.")
            self.connected = False # this peer may not work
            self.broken = True
