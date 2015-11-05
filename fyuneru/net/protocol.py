# -*- coding: utf-8 -*-

"""
Packets of Fyuneru

"""

import socket
from struct import pack, unpack

SIGN_DATAPACKET = 0x01

##############################################################################

# Raw IP Packet

class IPPacket:
    """This is an IP Packet parser in conjunction with VirtualNetworkInterface
    in `net` module. Use this class to get information about a packet's header.
    This class can be again stringified, and should produce the original
    buffer.
    """

    def __init__(self, tunbuf):
        """Read `tunbuf`, the buffer returned from TUN device. IFF_NO_PI is NOT
        set!"""
        self.__orig = tunbuf
        self.__parse(tunbuf)

    def __protocolName(self, proto):
        known = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
        }
        if known.has_key(proto): return known[proto]
        return 'Unknown'

    def __parse(self, buf):
        # meaning this is not raw packet, but with 4 bytes prefixed as in TUN
        # device defined
        if buf[:2] == '\x00\x00': buf = buf[4:] 

        ip_header = buf[0:20]
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
         
        version_ihl = iph[0]
        version = (version_ihl >> 4) & 0xF
        ihl = version_ihl & 0xF
         
        iph_length = ihl * 4
         
        ttl = iph[5]
        protocol = iph[6]
        s_addr = socket.inet_ntoa(iph[8])
        d_addr = socket.inet_ntoa(iph[9])

        payload = buf[iph_length:]

        self.version = version
        self.length = ihl
        self.TTL = ttl
        self.protocol = protocol
        self.protocolName = self.__protocolName(protocol)
        self.src = str(s_addr)
        self.dst = str(d_addr)
        
        self.payload = payload

    def __str__(self):
        return self.__orig
        

##############################################################################

# DataPacket

class DataPacketException(Exception):
    pass

class DataPacket:

    data = ''

    def __unpack(self, buf):
        if(len(buf) < 1):
            raise DataPacketException("Not a valid data packet.")
        sign = unpack('<B', buf[:1])[0]
        if sign != SIGN_DATAPACKET:
            raise DataPacketException("Not a valid data packet.")
        self.data = buf[1:]

    def __str__(self):
        """Pack this packet into a string."""
        buf = pack('<B', SIGN_DATAPACKET)
        buf += self.data
        return buf 
    
    def __init__(self, buf=None):
        """Read a packet with given `buf`, or construct an empty packet."""
        if None != buf:
            if type(buf) != str:
                raise DataPacketException("Not a valid data packet.")
            self.__unpack(buf)
            return

##############################################################################

# 

if __name__ == '__main__':
    packet = DataPacket()
    packet.data = 'abcdefg'
    print DataPacket(str(packet))
