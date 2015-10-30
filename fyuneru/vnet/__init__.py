# -*- coding: utf-8 -*-

import os
import fcntl
import struct
from logging import info, debug
from select import select

from pytun import TunTapDevice

TUNSETIFF = 0x400454ca  
IFF_TUN   = 0x0001


class VirtualNetworkInterface:

    mtu = 1200
    netmask = "255.255.255.0"

    def __init__(self, config):
        self.addr = config["ip"]
        self.dstaddr = config["dstip"]
        self.netmask = config["netmask"]

        self.__tun = os.open("/dev/net/tun", os.O_RDWR)
        tun = fcntl.ioctl(\
            self.__tun,
            TUNSETIFF,
            struct.pack("16sH", "t%d", IFF_TUN)
        )
        self.name = tun[:16].strip("\x00")  

    def up(self):
#        os.system("ip link set %s up" % (self.name))  
#        os.system("ip link set %s mtu %d" % (self.name, self.mtu))  
#        os.system("ip addr add %s dev %s" % (self.addr, self.name))  
        os.system("ifconfig %s inet %s netmask %s pointopoint %s" %\
            (self.name, self.addr, self.netmask, self.dstaddr)
        )
        os.system("ifconfig %s mtu %d up" % (self.name, self.mtu))
        
        info(\
            """%s: mtu %d  addr %s  netmask %s  dstaddr %s""" % \
            (\
                self.name, 
                self.mtu, 
                self.addr, 
                self.netmask, 
                self.dstaddr
            )
        )

    def fileno(self):
        return self.__tun

if __name__ == "__main__":
    vn = VirtualNetworkInterface({\
        "ip": "10.1.0.2",
        "dstip": "10.1.0.1",
        "netmask": "255.255.255.0",
    })
    vn.up()
    select([vn], [], [])
