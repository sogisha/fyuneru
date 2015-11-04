"""
Tool functions for IPC
"""
from select import select
from logging import info, debug, exception, error

class InitConfigWaiter:
    """For clients. Send an IPC query with `init` command and block execution,
    until a packet with proper answer is returned."""

    __queried = False

    def __queryFiller(self, packet):
        packet.question = 'init'
        packet.arguments = {"name": self.__ipc.name}
        return True

    def __infoReader(self, packet):
        try:
            if packet.title != 'init': return
            self.__queried = {
                "user": (packet.uid, packet.gid),
                "config": packet.config,
                "key": packet.key,
                "mode": packet.mode,
            }
        except Exception,e:
            exception(e)

    def __init__(self, ipc):
        self.__ipc = ipc
        ipc.onInfo(lambda p: self.__infoReader(p))

    def wait(self):
        info("Waiting for configuration.")
        i = 0
        while i < 5:
            self.__ipc.doQuery(lambda p: self.__queryFiller(p))
            r = select([self.__ipc], [], [], 1.0)[0]
            i += 1
            if len(r) < 1: continue
            self.__ipc.receive()
            if self.__queried: break
        if not self.__queried: return None
        return self.__queried
