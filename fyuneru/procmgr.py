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
        self.__processes[name] = proc

    def killall(self, tolerance=1.0):
        for each in self.__processes:
            self.kill(each, False)
        time.sleep(tolerance)
        for each in self.__processes:
            if None == self.__processes[each]:
                self.kill(each, True)

    def kill(self, name, force=False):
        if force:
            self.__processes[name].kill()
        else:
            self.__processes[name].terminate()

    def wait(self, name):
        self.__processes[name].wait()
