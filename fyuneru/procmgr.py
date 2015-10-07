# -*- coding: utf-8 -*-

import signal
import subprocess
import time

class ProcessManager:

    __processes = {}

    def __init__(self):
        signal.signal(signal.SIGTERM, self.killall)

    def new(self, name, cmd):
        proc = subprocess.Popen(cmd)
        __processes[name] = proc

    def killall(self):
        for each in self.__processes:
            self.kill(each, False)
        time.sleep(0.5)
        for each in self.__processes:
            if None == self.__processes[each]:
                self.kill(each, True)

    def kill(self, name, force=False):
        if not self.__processes.has_key(name):
            return
        if force:
            self.__processes[name].kill()
        else:
            self.__processes[name].terminate()
