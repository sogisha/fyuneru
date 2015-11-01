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
import sys

from drv_shadowsocks import proxyCommand as proxyCommandShadowsocks
#from drv_websocket   import proxyCommand as proxyCommandWebsocket  ## not usable
from drv_xmpp        import proxyCommand as proxyCommandXMPP

proxyCommands = {\
    "shadowsocks": proxyCommandShadowsocks,
#    "websocket": proxyCommandWebsocket,
    "xmpp": proxyCommandXMPP,
}


##############################################################################

class ProxyConfigException(Exception):
    pass

class ProxyConfig:
    
    def __init__(self, **args):
        self.pid = os.getpid()
        self.user = args["user"]
        self.basepath = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.baseKey = args["key"]
        self.proxyType = args["type"]
        self.proxyName = args["name"]
        self.proxyConfig = args["config"]

    def getInitCommand(self, mode, debug=False):
        if not mode in ['s', 'c']:
            raise ProxyConfigException("Mode should be either 'c' or 's'.")

        if proxyCommands.has_key(self.proxyType):
            return proxyCommands[self.proxyType](self, mode, debug)

        raise ProxyConfigException("Unsupported proxy type: %s" % \
            self.proxyType
        )
