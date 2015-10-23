# -*- coding: utf-8 -*-

from logging import info
from multiprocessing import Process, Pipe
from select import select

from pytun import TunTapDevice

from ..util import crypto


class VirtualNetworkInterface:
    
    def __init__(self, key, config):
        self.__tun = TunTapDevice()
        self.__tun.addr = config["ip"]
        self.__tun.dstaddr = config["dstip"]
        self.__tun.netmask = config["netmask"]
        self.__crypto = crypto.Crypto(key)

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

    def write(buf):
        self.__tun.write(self.__crypto.encrypt(buf))

    def read():
        return self.__crypto.decrypt(self.__tun.read(65536))



def __vNetProcess(pipe, key, config):
    tun = VirtualNetworkInterface(config)
    
    selects = {tun: "tun", pipe: "pipe"}
    while True:
        r = select(selects.keys(), [], [], 1.0)[0]
        if len(r) < 1: continue
        for each in r:
            if selects[each] == "tun":
                buf = each.read()
                if buf: pipe.send(buf)

            if selects[each] == "pipe":
                buf = each.recv()
                tun.write(buf)
    return        
   

def start(key, config):
    pipeA, pipeB = Pipe()
    proc = Process(target=__vNetProcess, args=(key, pipeB, config))
    proc.start()
    return (pipeA, proc)
