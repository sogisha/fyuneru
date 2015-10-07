# -*- coding: utf-8 -*-

import signal
import subprocess
import time


class ProcessManagerException(Exception):
    pass


class ProcessManager:

    __processes = {}

    def __init__(self):
        signal.signal(signal.SIGTERM, self.killall)

    def new(self, name, cmd):
        if self.__processes.has_key(name):
            raise ProcessManagerException(\
                "Child process already registered with name [%s]" % name)
        proc = subprocess.Popen(cmd)
        self.__processes[name] = proc

    def killall(self, tolerance=1.0):
        for each in self.__processes:
            self.kill(each, False)
        time.sleep(tolerance)
        for each in self.__processes:
            if None == self.__processes[each]:
                self.kill(each, True)

    def kill(self, name, force=False):
        try:
            if force:
                self.__processes[name].kill()
            else:
                self.__processes[name].terminate()
        except Exception,e:
            pass

    def wait(self, name):
        self.__processes[name].wait()
