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
from logging import log, debug, error, exception
from select import select
from multiprocessing import Process, Pipe

#from __shadowsocks import start as startCommandShadowsocks
from __xmpp        import start as startCommandXMPP

proxyCommands = {\
#    "shadowsocks": startCommandShadowsocks,
    "xmpp": startCommandXMPP,
}

##############################################################################

"""
Provides several tools for connecting core process and proxy process using
queues in multiprocessing module.
"""

class PipeDistributor:
    """
    Distribute traffic between an IO(selectable file) with pre-created
    subpipes by calling self.distribute(IO). This will start a loop.


                                                  __________
       Virtual Network Interface                 (          )
     __   (/dev/tun device)                     (  INTERNET  )
      |______________                            (__________)
      |  ..       o  |                                ^
      |     ...  o   |                               / \
      |_|||||||_||||_|                              /_ _\ Proxy Traffic
                                                     | |  (up and down)
           |  /|\                                    | |
           |   |                            +--------+-+-----------------+
           |   |          +--------->-------| PROXY 01         pipe.recv |
           |   |          |                 |                  pipe.send |>-+
           |   |          |                 +----------------------------+  |
           |   |          ^       ... +--->--------------------------------+|
           |   |          |  |  |     |     +----------------------------+ ||
           |   |        +----------------+  | PROXY 02         pipe.recv |<+|
           |   |        | Random Routing |  |                  pipe.send |>+|
          \|/  |        +----------------+  +----------------------------+ ||
                                |                                          ||
    +---------------------+     |                                          ||
    | CORE  QC.send       |-->--+                                       ___||
    |       QC.recv       |--<-----------------------------------------{----+
    +---------------------+
    """
    
    __subpipes = [] 

    def newSubpipe(self):
        connA, connB = Pipe()
        self.__subpipes.append(connA)
        return connB

    def distribute(self, io):
        subpipesCount = len(self.__subpipes)
        selects = [io] + self.__subpipes
        while True:
            try:
                r, _, __ = select(selects, [], [])
                for each in r:
                    if each == io:
                        # if received something from outside(i.e. local TUN device)    
                        debug("PipeDistributor: Core -->>>>-- Proxies")
                        buf = each.recv()
                        i = random.randrange(0, subpipesCount)
                        sendPipe = self.__subpipes[i]
                        sendPipe.send(buf)
                    else:
                        # if received something from subpipe(i.e. proxy)
                        debug("PipeDistributor: Core --<<<<-- Proxies")
                        buf = each.recv()
                        io.send(buf)
            except:
                break

##############################################################################

class ProxyProcessesException(Exception): pass

class ProxyProcesses:

    __processes = {}
    
    def __init__(self, **args):
        self.__pipeDistributor = PipeDistributor()

    def start(self, proxyconf):
        """Start a process using a return value from
        ..util.config.Configuration.getProxyConfig"""

        proxyType = proxyconf["type"]
        if proxyType != 'xmpp': return # XXX TODO remove this line. debug only.
        
        if not proxyCommands.has_key(proxyType):
            raise ProxyProcessesException("Unsupported proxy type: %s" % \
                proxyType
            )
        
        processName = proxyconf["name"]
        processMode = proxyconf["mode"]
        processFunc = proxyCommands[proxyType]
        processPipe = self.__pipeDistributor.newSubpipe()
        
        newProcess = Process(\
            target=processFunc, 
            args=(\
                processMode, 
                processPipe,
                proxyconf["config"]
            )
        )
        newProcess.start()

        self.__processes[processName] = newProcess

    def distribute(self, io):
        self.__pipeDistributor.distribute(io)
