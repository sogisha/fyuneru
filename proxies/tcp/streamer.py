#!/usr/bin/env python
# -*- coding: utf-8 -*-

CONTROLCHAR = '\\'

##############################################################################

escapeSelf = CONTROLCHAR * 2
escapeN = CONTROLCHAR + 'n'
def escape(string):
    global escapeSelf, escapeN, CONTROLCHAR
    string = string.replace(CONTROLCHAR, escapeSelf)
    string = string.replace('\n', escapeN)
    return string

def unescape(string):
    global CONTROLCHAR
    x = [i for i in string]
    for i in xrange(0, len(x) - 1):
        if x[i] != CONTROLCHAR:     # ignore general chars
            continue
        if x[i+1] == CONTROLCHAR:   # %% -> %
            x[i+1] = None
            i += 1
            continue
        if x[i+1] == 'n':           # %n -> \n
            x[i] = '\n'
            x[i+1] = None
            i += 1
            continue
    x = [i for i in x if i != None]
    return ''.join(x)

##############################################################################

class DatagramToStream:
    __buf = ''

    def __init__(self):
        pass

    def write(self, buf):
        self.__buf += escape(buf) + '\n'

    def read(self, size=None):
        if None == size:
            ret = self.__buf
            self.__buf = ''
        else:
            if type(size) != int or size <= 0:
                raise Exception('Size must be an integer and greater as 0.')
            ret = self.__buf[:size]
            self.__buf = self.__buf[size:]
        return ret

class StreamToDatagram:
    __buf = '\n'
    __parsed = []

    def __init__(self):
        pass

    def write(self, buf):
        self.__buf += buf
        self.__parse()

    def read(self):
        if len(self.__parsed) < 1:
            return None
        r = self.__parsed[0]
        self.__parsed = self.__parsed[1:]
        return r

    def __parse(self):
        l = len(self.__buf)
        p = None 
        cut = False
        for i in xrange(0, l):
            char = self.__buf[i]
            if char == '\n':
                if None == p:
                    p = i
                else:
                    self.__parsed.append(unescape(self.__buf[p+1:i]))
                    p = i
                    cut = True
        if cut:
            self.__buf = self.__buf[p:]

##############################################################################

if __name__ == '__main__':
    import random
    packer = DatagramToStream()
    unpacker = StreamToDatagram()

    send = [''.join([chr(random.randrange(0, 256)) for i in xrange(0, 1000)]) for c in xrange(0, 30)]
    #send = ['abcde', 'apple']

    for each in send:
        packer.write(each)

    stream = packer.read()

    print 'Stream len: ', len(stream)

    unpacker.write(stream)

    recv = []
    while True:
        g = unpacker.read()
        if None == g:
            break
        recv.append(g)

    print 'Received: ', len(recv)
    
    #print repr(stream)
    #print recv

    if len(recv) != len(send):
        print "Not all datagrams received."
        exit()

    for i in xrange(0, len(recv)):
        if recv[i] != send[i]:
            print "Not match: %5d, recv %5d, orig %5d" % (i, len(recv[i]), len(send[i]))
