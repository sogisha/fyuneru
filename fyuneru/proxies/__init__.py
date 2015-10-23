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
from multiprocessing import Process, Queue


from __shadowsocks import start as startCommandShadowsocks
from __xmpp        import start as startCommandXMPP

proxyCommands = {\
    "shadowsocks": startCommandShadowsocks,
    "xmpp": startCommandXMPP,
}


##############################################################################

class ProxyProcessException(Exception): pass

class ProxyProcessManager:

    __processes = {}
    __proxy2core = None
    
    def __init__(self, **args):
        self.__proxy2core = Queue()

    def start(self, proxyconf):
        """Start a process using a return value from
        ..util.config.Configuration.getProxyConfig"""

        proxyType = proxyconf["type"]
        
        if not proxyCommands.has_key(proxyType):
            raise ProxyProcessException("Unsupported proxy type: %s" % \
                proxyType
            )
        
        processName = proxyconf["name"]
        processMode = proxyconf["mode"]
        processFunc = proxyCommands(proxyconf)
        processQueue = Queue()
        
        newProcess = Process(\
            target=processFunc, 
            args=(\
                processMode, 
                (self.__proxy2core, processQueue),
                config=proxyconf["config"]
            )
        )
        newProcess.start()

        self.__processes[name] = (processPipe, newProcess)

    def __removeProcesses(self):
        # remove processes that are ended
        removeList = []
        for each in self.__processes:
            _, proc = self.__processes[each]
            if not proc.is_alive():
                removeList.append(each)
        for each in removeList:
            del self.__processes[each]

    def send(self, buf):
        """Non-blocks sending a buffer to randomly one of the started
        processes."""
        self.__removeProcesses()
        try:
            # this may not always work, since process may still now exit
            keys = self.__processes.keys()
            key = keys[random.randrange(0, len(keys))]
            queue, _ = self.__processes[key]
            queue.put(buf)
        except Exception,e
            print e

    def recv(self):
        """Non-blocks retrieving a buffer returned from one of the started
        processes."""
        try:
            buf = self.__proxy2core.get(False)
        except:
            return None
        return buf
