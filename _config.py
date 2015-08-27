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
        
        if type(core["key"]) != str:
            raise ConfigFileException("core.key is invalid.")
        self.key = core["key"]

        if not core["server"].has_key("ip"):
            raise ConfigFileException("core.server.ip must be specified.")
        if not core["client"].has_key("ip"):
            raise ConfigFileException("core.client.ip must be specified.")
        self.serverIP = core["server"]["ip"]
        self.clientIP = core["client"]["ip"]

        
        

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


##############################################################################

if __name__ == "__main__":
    config = Configuration(open('./config.json', 'r').read())
    print config
