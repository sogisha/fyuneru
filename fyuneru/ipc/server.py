# -*- coding: utf-8 -*-

"""
Internal Fyuneru Socket for Proxy Processes

A fyuneru socket basing on UDP socket is defined. It is always a listening UDP
socket on a port in local addr, which does automatic handshake with given
internal magic word, and provides additionally abilities like encryption
underlays, traffic statistics, etc.
"""

import os
from logging import debug, info, warning, error, exception
from time import time
from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM
import random

from ..util.crypto import Crypto, Authenticator
from __protocol import * 

IPCPort = 64089

##############################################################################

class InternalSocketServer:

    __sockpath = None
    __sock = None
    
    local = None
    IPCKey = None
    peers = {}

    __answerFunctions = {} # for IPC query/info service

    def __init__(self, key):
        self.IPCKey = os.urandom(32)

        self.__crypto = Crypto(key)
        self.__authenticator = Authenticator(self.IPCKey)
        self.local = ("127.0.0.1", IPCPort)
        
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind(self.local)

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

    def __sendPacket(self, packet, to):
        """Send a packet class to a destination using local socket."""
        s = self.__authenticator.sign(str(packet))
        self.__sock.sendto(s, to)

    def __recvBuffer(self, buf, sender):
        """Receive a buffer, unpack into packet, and dispatch it to different
        handlers. Returns buffer when unpacked is a DataPacket. Otherwise
        None."""
        # See if is a data packet, which is special.
        buf = self.__authenticator.verify(buf)
        if not buf: return None # signature check failed
        packet = loadBufferToPacket(buf)
        if not packet: return None
        if isinstance(packet, DataPacket): return packet.buffer

        # If not, call different handlers to handle this.
        if isinstance(packet, HeartbeatPacket):
            self.__handleHeartbeatPacket(packet, sender)
            return None
        if isinstance(packet, QueryPacket):
            self.__handleQueryPacket(packet, sender)
            return None

    # ---------- inner handlers for different packets

    def __handleHeartbeatPacket(packet, sender):
        # If this is a greeting word, register this as a new connected peer
        # and answer.
        self.__registerPeer(sender)
        self.__sendPacket(packet, sender)

    def __handleQueryPacket(packet, sender):
        question = packet.question
        if self.__answerFunctions.has_key(question):
            # a new answer formular
            answer = InfoPacket()
            # call handler func to fill in the answer formular
            self.__answerFunctions[question](packet.arguments, answer)
            # send the answer back
            self.__sendPacket(answer, sender)

    # ---------- public functions

    def onQuery(self, question, answerfunc):
        self.__answerFunctions[question] = answerfunc

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

        buf = self.__recvBuffer(buf, sender) # pre handling this buffer
        if not buf: return None # digested within other mechanism. exit.

        # Otherwise, this is data buffer and has to be decrypted correctly.
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
            packet = DataPacket()
            packet.buffer = encryption
            self.__sendPacket(packet, peer)
        except Exception,e:
            exception(e) # for debug
            warning(\
                ("Failed sending to proxy listening at %s:%d." % peer) +
                "This proxy will be removed."
            )
            self.peers[peer] = False # this peer may not work
