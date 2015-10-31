# -*- coding: utf-8 -*-

from logging import info, debug
from multiprocessing import Process, Pipe
from select import select

from pytun import TunTapDevice

from ..util import crypto, droproot, debugging



class VirtualNetworkInterface:
    
    def __init__(self, config):
        self.__tun = TunTapDevice()
        self.__tun.addr = config["ip"]
        self.__tun.dstaddr = config["dstip"]
        self.__tun.netmask = config["netmask"]

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

    def write(self, buf):
        self.__tun.write(buf)

    def read(self):
        return self.__tun.read(65536)



def __vNetProcess(proxyIO, config):
    tun = VirtualNetworkInterface(config)
    tun.up()
    droproot.dropRoot(*config["user"])

    crypt = crypto.Crypto(config["key"])
    encrypt, decrypt = crypt.encrypt, crypt.decrypt
    
    while True:
        r = select([proxyIO, tun], [], [])[0]
        for each in r:
            if each == tun:
                buf = tun.read()
                proxyIO.send(encrypt(buf))
                debug("SEND: \n%s\n" % debugging.showPacket(buf))
            if each == proxyIO:
                buf = proxyIO.recv()
                buf = decrypt(buf)
                if not buf: continue
                tun.write(buf)
                debug("RECV: \n%s\n" % debugging.showPacket(buf))
    return        
   

def start(proxyIO, config):
    info("Creating core process...")
    proc = Process(target=__vNetProcess, args=(proxyIO, config))
    proc.start()
    info("Core process started.")
    return proc 
