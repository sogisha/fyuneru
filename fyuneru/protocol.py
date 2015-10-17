# -*- coding: utf-8 -*-

"""
Packets of Fyuneru

"""

from struct import pack, unpack

SIGN_DATAPACKET = 0x01

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
