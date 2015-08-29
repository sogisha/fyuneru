# -*- coding: utf-8 -*-

"""
class ProxyConfig

Receives proxy configurations and return the command for initiating the
process.
"""

class ProxyConfigException(Exception):
    pass

##############################################################################

class ProxyConfig:
    def __initWebsocket(self, mode):
        proxyCommandWebsocket = ['node']
        if mode == 's':
            proxyCommandWebsocket += [
                './proxies/websocket/server.js', 
                str(self.proxyConfig["server"]["webport"]),
            ]
            proxyCommandWebsocket.append(str(self.portServer))
        else:
            proxyCommandWebsocket += [
                './proxies/websocket/client.js', 
                "%s:%s" % (
                    str(self.proxyConfig["server"]["ip"]),
                    str(self.proxyConfig["server"]["webport"]),
                ),
            ]
            proxyCommandWebsocket.append(str(self.portClient))
        return proxyCommandWebsocket

    def __init__(self, **args):
        self.proxyType = args["type"]
        self.portClient = args["clientPort"]
        self.portServer = args["serverPort"]
        self.proxyConfig = args["config"]

    def getInitCommand(self, mode):
        if not mode in ['s', 'c']:
            raise ProxyConfigException("Mode should be either 'c' or 's'.")

        if self.proxyType == 'websocket':
            return self.__initWebsocket(mode)

        if self.proxyType == 'shadowsocks':
            return [] 
        
        raise ProxyConfigException("Unsupported proxy type: %s" % \
            self.proxyType
        )
