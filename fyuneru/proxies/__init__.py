# -*- coding: utf-8 -*-

"""
class ProxyProcess

Receives proxy configurations and return the class for initiating the process.

This class manages the drivers of different types of proxies. To write a new
proxy, a driver is necessary to be included here. 

Some proxy methods(e.g. Shadowsocks) support additional encryption. The
corresponding keys for that purpose is calculated using the core key, so that
the user doesn't have to maintain them on their own.
"""
import os
import sys
import random # replace with secure randomness
from logging import log, debug, error
from multiprocessing import Process

from ..util.queuecenter import QueueCenter


#from __shadowsocks import start as startCommandShadowsocks
from __xmpp        import start as startCommandXMPP

proxyCommands = {\
#    "shadowsocks": startCommandShadowsocks,
    "xmpp": startCommandXMPP,
}


##############################################################################

class ProxyProcessException(Exception): pass

class ProxyProcessManager:

    __processes = {}
    
    def __init__(self, **args):
        self.__queueCenter = QueueCenter()

    def start(self, proxyconf):
        """Start a process using a return value from
        ..util.config.Configuration.getProxyConfig"""

        proxyType = proxyconf["type"]
        if proxyType != 'xmpp': return # XXX TODO remove this line. debug only.
        
        if not proxyCommands.has_key(proxyType):
            raise ProxyProcessException("Unsupported proxy type: %s" % \
                proxyType
            )
        
        processName = proxyconf["name"]
        processMode = proxyconf["mode"]
        processFunc = proxyCommands[proxyType]
        processQueuePair = self.__queueCenter.newProcessQueuePair()
        
        newProcess = Process(\
            target=processFunc, 
            args=(\
                processMode, 
                processQueuePair,
                proxyconf["config"]
            )
        )
        newProcess.start()

        self.__processes[processName] = newProcess

    def __removeProcesses(self):
        # remove processes that are ended
        removeList = []
        for each in self.__processes:
            proc = self.__processes[each]
            if not proc.is_alive():
                removeList.append(each)
        for each in removeList:
            del self.__processes[each]

    def send(self, buf):
        """Non-blocks sending a buffer to randomly one of the started
        processes."""
        self.__removeProcesses()
        return self.__queueCenter.send(buf)

    def recv(self):
        """Non-blocks retrieving a buffer returned from one of the started
        processes."""
        return self.__queueCenter.recv() 

    def process(self):
        self.__queueCenter.process()
