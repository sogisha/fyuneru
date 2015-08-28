# -*- coding: utf-8 -*-

from distutils.version import StrictVersion
from json import loads

VERSION_REQUIREMENT = "1.0" # required version of `config.json`

##############################################################################

class ConfigFileException(Exception):
    pass

##############################################################################

class Configuration:

    def __checkKeyExistence(self, parentDict, *keys):
        for each in keys:
            if not parentDict.has_key(each):
                return False
        return True

    def __loadCore(self, core):
        # parse json.core and save to class attributes
        
        # get key for cryptography
        self.key = str(core["key"])
        if type(self.key) != str:
            raise ConfigFileException("core.key is invalid.")

        # get IP for server and client
        if not core["server"].has_key("ip"):
            raise ConfigFileException("core.server.ip must be specified.")
        if not core["client"].has_key("ip"):
            raise ConfigFileException("core.client.ip must be specified.")
        self.serverIP = core["server"]["ip"]
        self.clientIP = core["client"]["ip"]

    def __loadProxyAllocations(self, core, proxies):
        # get and validate proxy and ports allocations
        self.__proxies = {}

        udpAllocations = core["udpalloc"]
        for allocName in udpAllocations:
            if not proxies.has_key(allocName):
                raise ConfigFileException(\
                    "Proxy method [%s] not defined" % allocName
                )
            proxyConfig = proxies[allocName]
            allocConfig = udpAllocations[allocName]
            self.__proxies[allocName] = {
                "ports": {
                    "server": allocConfig["server"],
                    "client": allocConfig["client"],
                },
                "config": proxyConfig
            }

    def listProxies(self):
        return self.__proxies.keys()

    def getProxyConfig(self, name):
        if not self.__proxies.has_key(name):
            raise ConfigFileException("No such proxy method defined.")
        proxyConfig = self.__proxies[name]["config"]
        return None # XXX TODO return accordingly generated command for initiating this proxy

    def getProxyPorts(self, name):
        if not self.__proxies.has_key(name):
            raise ConfigFileException("No such proxy method defined.")
        return self.__proxies[name]["ports"]

    def __init__(self, config):
        # try load the configuration file string, and parse into JSON.
        try:
            json = loads(config)
        except Exception,e:
            raise ConfigFileException("config.json parse error.")

        # read config file version declaration
        jsonVersion = "0.0.0"
        if json.has_key("version"):
            jsonVersion = json["version"]
        if StrictVersion(jsonVersion) < StrictVersion(VERSION_REQUIREMENT):
            raise ConfigFileException("config.json version too old.")

        # check existence of 'core' and 'proxies' entry
        if not self.__checkKeyExistence(json, 'core', 'proxies'):
            raise ConfigFileException("config.json incomplete.")

        # check entries of core
        jsonCore = json["core"]
        if not self.__checkKeyExistence(\
            jsonCore, 
            'server',
            'client',
            'key',
            'udpalloc'
        ):
            raise ConfigFileException("config.json incomplete.")
        self.__loadCore(jsonCore)

        # check for proxy allocations
        jsonProxies = json["proxies"]
        self.__loadProxyAllocations(jsonCore, jsonProxies)


##############################################################################

if __name__ == "__main__":
    config = Configuration(open('./config.json', 'r').read())
    print config
