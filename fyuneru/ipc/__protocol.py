"""
IPC used data packets generation and parsing
============================================

This module defines several data packet classes, and a trying function for
reading a buffer.
"""

import pickle

TYPE_DATAPACKET = 0x01
TYPE_HEARTBEAT  = 0x02
TYPE_QUERY      = 0x03
TYPE_INFO       = 0x04

class WrongTypeOfPacketException(Exception): pass

##############################################################################

# Data packet, carries a buffer.

class DataPacket:

    buffer = ''
    
    def __init__(self, buf=None):
        if None == buf: return
        if ord(buf[0]) != TYPE_DATAPACKET: raise WrongTypeOfPacketException()
        self.buffer = buf[1:]

    def __str__(self):
        return chr(TYPE_DATAPACKET) + self.buffer

# Heartbeat packet, carries nothing.

class HeartbeatPacket:
    
    def __init__(self, buf=None):
        if None == buf: return
        if ord(buf[0]) != TYPE_HEARTBEAT: raise WrongTypeOfPacketException()

    def __str__(self):
        return \
            chr(TYPE_HEARTBEAT) +\
            "Across the Great Wall, we can reach every corner in the world."

# Query packet, carries a question text.

class QueryPacket:

    question = ''
    arguments = {}

    def __init__(self, buf=None):
        if None == buf: return
        if ord(buf[0]) != TYPE_QUERY: raise WrongTypeOfPacketException()
        obj = pickle.loads(buf[1:])
        self.question = obj["question"]
        self.arguments = obj["arguments"]

    def __str__(self):
        obj = {"question": self.question, "arguments": self.arguments}
        return chr(TYPE_QUERY) + pickle.dumps(obj)

# Info packet, carries an info text.

class InfoPacket:

    def __init__(self, buf=None):
        if None == buf: return
        if ord(buf[0]) != TYPE_INFO: raise WrongTypeOfPacketException()
        self.__dict__ = pickle.loads(buf[1:])

    def __setattr__(self, name, value):
        print "set attr: %s" % name
        self.__dict__[name] = value

    def __getattr__(self, name):
        return getattr(self.__dict__, name)

    def __str__(self):
        return chr(TYPE_INFO) + pickle.dumps(self.__dict__)

##############################################################################

def loadBufferToPacket(buf):
    tries = [DataPacket, HeartbeatPacket, QueryPacket, InfoPacket]
    success = False
    for packetClass in tries:
        try:
            loaded = packetClass(buf)
            success = True
            break
        except WrongTypeOfPacketException:
            continue
        except Exception,e:
            raise e
    if success: return loaded
    return None

##############################################################################

__all__ = ['DataPacket', 'HeartbeatPacket', 'QueryPacket', 'InfoPacket', 'loadBufferToPacket']

if __name__ == '__main__':
    pin1 = InfoPacket()
    pin2 = InfoPacket()

    pin1.attr1 = '1'
    pin1.attr2 = '2'

    pin2.attr1 = '3'
    pin2.attr2 = '4'

    pin3 = InfoPacket(str(pin1))
    print pin3.attr1
    print pin3.attr2

    pin4 = InfoPacket(str(pin2))
    print pin4.attr1
    print pin4.attr2
