# -*- coding: utf-8 -*-

import signal
import subprocess
import time
from logging import debug, info, warning, error


class ProcessManagerException(Exception):
    pass


class ProcessManager:

    __processes = {}
    __commands = {}

    def __init__(self):
        signal.signal(signal.SIGTERM, self.killall)

    def __pollAll(self):
        for each in self.__processes:
            try:
                self.processes[each].poll()
            except:
                pass

    def __startProcess(self, name, command):
        info("ProcessManager starting [%s]: %s" % (name, " ".join(command)))
        proc = subprocess.Popen(command)
        self.__processes[name] = proc
        self.__commands[name] = command

    def new(self, name, command):
        if self.__processes.has_key(name):
            raise ProcessManagerException(\
                "Child process already registered with name [%s]" % name)
        self.__startProcess(name, command)

    def killall(self, tolerance=1.0):
        for each in self.__processes:
            self.kill(each, tolerance)

    def kill(self, name, tolerance=1.0):
        if not self.__processes.has_key(name): return True
        sigtermSuccess = False
        if tolerance:
            try:
                info("ProcessManager stopping [%s] gracefully." % name)
                self.__processes[name].terminate()
                time.sleep(1.0)
                self.__processes[name].poll()
                sigtermSuccess = (self.__processes[name].returncode != None)
            except:
                pass
        if sigtermSuccess:
            info("ProcessManager confirmed stop of [%s]." % name)
            return True
        warning("ProcessManager couldn't stop [%s] with tolerance." % name)
        try:
            self.__processes[name].kill()
            info("ProcessManager killed [%s]." % name)
            return True
        except Exception,e:
            error(("ProcessManager cannot stop [%s]. " % name) + \
                "It may has been already killed. Giving up.")
            return False

    def restart(self, name, tolerance=1.0):
        if not self.__commands.has_key(name): return False
        if not self.kill(name, tolerance):
            return False
        command = self.__commands[name]
        self.__startProcess(name, command)

    def wait(self, name):
        self.__processes[name].wait()
