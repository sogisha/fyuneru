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

    def __init__(self, key):
        self.__crypto = Crypto(key)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind(("127.0.0.1", IPCPort))

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def __registerPeer(self, addrTuple, timestamp=None):
        """Register a peer's activity. This implies we have heard from this
        peer. If timestamp is given, it will be used to update the last network
        reception time."""
        now = time()

        if not self.peers.has_key(addrTuple):
            self.peers[addrTuple] = {\
                "recv": False,
                "send": False,
                "heartbeat": now,
            }
            return

        if timestamp: self.peers[addrTuple]["recv"] = timestamp
        self.peers[addrTuple]["heartbeat"] = now

    def __choosePeer(self):
        """Choose a peer randomly. This implies we are going to send a packet
        to this peer, and thus the sending timing will be updated."""
        possiblePeers = [i for i in self.peers if self.peers[i] != False]
        if len(possiblePeers) < 1: return None
        peer = possiblePeers[random.randrange(0, len(possiblePeers))]
        self.peers[peer]["send"] = time()
        return peer

    def close(self):
        # close socket
        debug("Internal socket shutting down...")
        try:
            self.__sock.close()
        except Exception,e:
            error("Error closing socket.")
            exception(e)

    def clean(self):
        # reserved for doing clean up jobs relating to the peer delays
        removeList = []
        now = time()
        for each in self.peers:
            if not self.peers[each]:
                # if peer has been marked as False, because of errors, etc
                removeList.append(each)
                continue
            # if we have not heard from peer for some while, take it as stale
            if now - self.peers[each]["heartbeat"] > 5:
                removeList.append(each)
        if len(removeList) > 0:
            for each in removeList:
                # delete peers: forget them(no more tasks will be assigned)
                self.peers[each] = False
                del self.peers[each]
            warning(\
                "Following proxies are removed due to irresponsibility: \n" +
                " \n".join(["%s:%d" % i for i in removeList])
            )

    def receive(self):
        buf, sender = self.__sock.recvfrom(65536)

        if buf.strip() == UDPCONNECTOR_WORD:
            # If this is a greeting word, register this as a new connected peer
            # and answer
            self.__registerPeer(sender)
            self.__sock.sendto(UDPCONNECTOR_WORD, sender)
            return None

        # Otherwise, this is data packet and has to be decrypted correctly.
        decryption = self.__crypto.decrypt(buf)
        if not decryption: return None

        # Decrypted data must be also good formated.
        if len(decryption) < 8: return None
        header = decryption[:8]
        timestamp = unpack('<d', header)[0]
        if timestamp > time(): return None # don't fool me
        buf = decryption[8:]

        # Only then we will recognize this as a legal status update from this
        # peer. Refresh the peer record with updated receiving timings.
        self.__registerPeer(sender, timestamp)

        return buf 

    def send(self, buf):
        # Choose a peer randomly
        peer = self.__choosePeer()
        if not peer: 
            error("Not even one proxy found. Dropping a packet.")
            return

        # Prepare for the data that's going to be sent to this peer
        header = pack('<d', time())
        encryption = self.__crypto.encrypt(header + buf)

        # Send to this peer. If anything goes wrong, mark this peer as False
        try:
            self.__sock.sendto(encryption, peer)
        except Exception,e:
            exception(e) # for debug
            warning(\
                ("Failed sending to proxy listening at %s:%d." % peer) +
                "This proxy will be removed."
            )
            self.peers[peer] = False # this peer may not work

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
