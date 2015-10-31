# -*- coding: utf-8 -*-

from logging import info, debug
from select import select

from pytun import TunTapDevice

from ..util import crypto, droproot, debugging



class VirtualNetworkInterface:

    """This is a weird NetworkInterface, which nevers talks to the other
    part of our program with plaintext."""
    
    def __init__(self, config):
        self.__tun = TunTapDevice()
        self.__tun.addr = config["ip"]
        self.__tun.dstaddr = config["dstip"]
        self.__tun.netmask = config["netmask"]
        crypt = crypto.Crypto(config["key"])
        self.__encrypt, self.__decrypt = crypt.encrypt, crypt.decrypt

    def up(self):
        self.__tun.up()
        info(\
            """%s: mtu %d  addr %s  netmask %s  dstaddr %s""" % \
            (\
                self.__tun.name, 
                self.__tun.mtu, 
                self.__tun.addr, 
                self.__tun.netmask, 
                self.__tun.dstaddr
            )
        )

    def __getattr__(self, name):
        return getattr(self.__tun, name)

    def send(self, buf):
        """Send the buffer, which was received from proxy, to local system."""
        buf = self.__decrypt(buf)
        if not buf: return
        debug("Network: SEND %d plain bytes." % len(buf))
        self.__tun.write(buf)

    def recv(self):
        """Receive a buffer from local system and encrypt it before emits."""
        buf = self.__tun.read(65536)
        debug("Network: RECV %d plain bytes." % len(buf))
        return self.__encrypt(buf)
