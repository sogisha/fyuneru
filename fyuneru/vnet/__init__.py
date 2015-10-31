# -*- coding: utf-8 -*-

from logging import info, debug
from select import select

from pytun import TunTapDevice

from ..util import crypto, droproot, debugging



class VirtualNetworkInterface:
    
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

    def fileno(self):
        return self.__tun.fileno()

    def send(self, buf):
        self.__tun.write(self.__encrypt(buf))

    def recv(self):
        buf = self.__tun.read(65536)
        return self.__decrypt(buf)



def start(config):
    tun = VirtualNetworkInterface(config)
    tun.up()
    return tun
