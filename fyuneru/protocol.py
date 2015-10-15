# -*- coding: utf-8 -*-

"""
Packets of Fyuneru

"""

from struct import pack, unpack
from time import time

class DataPacketException(Exception):
    pass

##############################################################################

class DataPacket:

    timestamp = 0 
    data = ''

    def __unpack(self, buf):
        if(len(buf) < 8):
            raise DataPacketException("Not a valid packet. Length < 8.")
        self.timestamp = unpack('<d', buf[:8])[0]
        self.data = buf[8:]

    def __str__(self):
        """Pack this packet into a string."""
        bufTimestamp = pack('<d', self.timestamp)
        return bufTimestamp + self.data
    
    def __init__(self, buf=None):
        """Read a packet with given `buf`, or construct an empty packet."""
        if None != buf:
            if type(buf) != str:
                raise DataPacketException("Not a valid packet. Str expected.")
            self.__unpack(buf)
            return
        self.timestamp = time()



if __name__ == '__main__':
    packet = DataPacket()
    print str(packet)
