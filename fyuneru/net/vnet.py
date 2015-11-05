# -*- coding: utf-8 -*-

import os
import fcntl
import struct
from logging import info, debug, critical, exception
from select import select

TUNSETIFF = 0x400454ca  
IFF_TUN   = 0x0001      # Set up TUN device
IFF_TAP   = 0x0002      # Set up TAP device
IFF_NO_PI = 0x1000      # Without this flag, received frame will have 4 bytes
                        # for flags and protocol(each 2 bytes)

class VirtualNetworkInterfaceException(Exception): pass

class VirtualNetworkInterface:

    mtu = 1200
    netmask = "255.255.255.0"

    def __getTUNDeviceLocation(self):
        if os.path.exists("/dev/net/tun"): return "/dev/net/tun"
        if os.path.exists("/dev/tun"): return "/dev/tun"
        critical("TUN/TAP device not found on this OS!")
        raise VirtualNetworkInterfaceException("No TUN/TAP device.")

    def __init__(self, ip, dstip, netmask="255.255.255.0"):
        self.addr = ip 
        self.dstaddr = dstip
        self.netmask = netmask

        try:
            self.__tun = os.open(self.__getTUNDeviceLocation(), os.O_RDWR)
            tun = fcntl.ioctl(\
                self.__tun,
                TUNSETIFF,
                struct.pack("16sH", "fyuneru-%d", IFF_TUN)
            )
        except Exception,e:
            exception(e)
            raise VirtualNetworkInterfaceException(\
                "Cannot set TUN/TAP device."
            )
        self.name = tun[:16].strip("\x00")  

    def up(self):
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

    def write(self, buf):
        os.write(self.__tun, buf)

    def read(self, size=65536):
        return os.read(self.__tun, size)

    def close(self):
        try:
            os.close(self.__tun)
        except:
            pass

if __name__ == "__main__":
    vn = VirtualNetworkInterface({\
        "ip": "10.1.0.2",
        "dstip": "10.1.0.1",
        "netmask": "255.255.255.0",
    })
    vn.up()
    select([vn], [], [])
