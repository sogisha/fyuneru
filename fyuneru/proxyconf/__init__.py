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
import hashlib
import hmac

class ProxyConfigException(Exception):
    pass

##############################################################################

class ProxyConfig:
    def __initWebsocket(self, mode):
        proxyCommand = ['node']
        if mode == 's':
            proxyCommand += [
                os.path.join(self.__proxyBase, 'websocket', 'server.js'),
                str(self.proxyConfig["server"]["port"]),
            ]
            proxyCommand.append(str(self.portServer))
        else:
            proxyCommand += [
                os.path.join(self.__proxyBase, 'websocket', 'client.js'),
                "%s:%s" % (
                    str(self.proxyConfig["server"]["ip"]),
                    str(self.proxyConfig["server"]["port"]),
                ),
            ]
            proxyCommand.append(str(self.portClient))
        return proxyCommand

    def __initShadowsocks(self, mode):
        sharedsecret= hmac.HMAC(\
            'shadowsocks',
            self.__baseKey,
            hashlib.sha256
        ).digest().encode('base64').strip()
        if mode == 's':
            proxyCommand = [
                'ssserver',
                '-k', sharedsecret,
                '-m', 'aes-256-cfb',
                '-s', self.proxyConfig["server"]["ip"],
                '-p', str(self.proxyConfig["server"]["port"]),
            ]
        else:
            proxyCommand = [
                'python',
                os.path.join(self.__proxyBase, 'shadowsocks', 'client.py'),
                '-k', sharedsecret,
                '-s', self.proxyConfig["server"]["ip"],
                '-p', str(self.proxyConfig["server"]["port"]),
                '-b', '127.0.0.1',
                '-l', str(self.proxyConfig["client"]["port"]),
                '-m', 'aes-256-cfb',
                str(self.portClient), # local  udp listening port
                '127.0.0.1',          # remote udp listening addr
                str(self.portServer), # remote udp listening port
            ]
        return proxyCommand

    def __init__(self, **args):
        if args.has_key("base"):
            self.__proxyBase = args["base"]
        else:
            self.__proxyBase = os.path.join(".", "proxies")
        self.__baseKey = args["key"]
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
            return self.__initShadowsocks(mode)
        
        raise ProxyConfigException("Unsupported proxy type: %s" % \
            self.proxyType
        )
