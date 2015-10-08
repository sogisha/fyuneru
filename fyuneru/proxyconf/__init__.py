# -*- coding: utf-8 -*-

"""
class ProxyConfig

Receives proxy configurations and return the command for initiating the
process.

This class manages the drivers of different types of proxies. To write a new
proxy, a driver is necessary to be included here. 

Some proxy methods(e.g. Shadowsocks) support additional encryption. The
corresponding keys for that purpose is calculated using the core key, so that
the user doesn't have to maintain them on their own.
"""
import os

from drv_shadowsocks import proxyCommand as proxyCommandShadowsocks
from drv_websocket   import proxyCommand as proxyCommandWebsocket

proxyCommands = {\
    "shadowsocks": proxyCommandShadowsocks,
    "websocket": proxyCommandWebsocket,
}


##############################################################################

class ProxyConfigException(Exception):
    pass

class ProxyConfig:
    
    def __init__(self, **args):
        if args.has_key("base"):
            self.proxyBase = args["base"]
        else:
            self.proxyBase = os.path.join(".", "proxies")
        self.baseKey = args["key"]
        self.proxyType = args["type"]
        self.portClient = args["clientPort"]
        self.portServer = args["serverPort"]
        self.proxyConfig = args["config"]

    def getInitCommand(self, mode):
        if not mode in ['s', 'c']:
            raise ProxyConfigException("Mode should be either 'c' or 's'.")

        if proxyCommands.has_key(self.proxyType):
            return proxyCommands[self.proxyType](self, mode)

        raise ProxyConfigException("Unsupported proxy type: %s" % \
            self.proxyType
        )
