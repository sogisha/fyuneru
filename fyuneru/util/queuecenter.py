"""
Provides several tools for connecting core process and proxy process using
queues in multiprocessing module.
"""

from Queue import Empty, Full
from multiprocessing import Queue
from uuid import uuid1
from logging import info, debug, exception
import random

class ProcessQueuePair:
    """This class provides a queue pair that can be passed to process as an
    object. This class has to be initialized by a QueueCenter instance which
    puts itself as the second parameter in __init__ function. The `send` and
    `recv` functions are for the processes."""
    
    def __init__(self, regfunc, label):
        self.__core2proc = Queue()
        self.__proc2core = Queue()
        regfunc(\
            self.__core2proc,
            self.__proc2core,
            label
        )

    def send(self, obj):
        """Puts an object into the proc2core queue."""
        try:
            self.__proc2core.put_nowait(obj)
        except Full:
            return False
        return True

    def recv(self):
        """Reads an object from the core2proc queue."""
        try:
            return self.__core2proc.get_nowait()
        except Empty:
            return None
        

class QueueCenter:
    """This class provides a all-in-one solution for both core and processes.
    The core process always gets a `recv` and `send` function, with processes
    must firstly `apply` for a pair of them providing their own names. 

    On the packets sent by the core process using `send` function there will be
    also a random routing scheme applied, which decides a proxy for this
    packet. The proxy then use its own `recv` function to get this packet.

    The proxy, who received a packet using its own mechanism, has to use its
    `send` function to deliver this packet to our system. The core process will
    use its `recv` function to get it.

                                                  __________
       Virtual Network Interface                 (          )
     __   (/dev/tun device)                     (  INTERNET  )
      |______________                            (__________)
      |  ..       o  |                                ^
      |     ...  o   |                               / \
      |_|||||||_||||_|                              /_ _\ Proxy Traffic
                                                     | |  (up and down)
           |  /|\                                    | |
           |   |                            +--------+-+-----------------+
           |   |          +--------->-------| PROXY 01    ProcQPair.recv |
           |   |          |                 |             ProcQPair.send |>-+
           |   |          |                 +----------------------------+  |
           |   |          ^       ... +--->--------------------------------+|
           |   |          |  |  |     |     +----------------------------+ ||
           |   |        +----------------+  | PROXY 02  ProcQPair.recv   |<+|
           |   |        | Random Routing |  |           ProcQPair.send   |>+|
          \|/  |        +----------------+  +----------------------------+ ||
                                |                                          ||
    +---------------------+     |                                          ||
    | CORE  QC.send       |-->--+                                       ___||
    |       QC.recv       |--<-----------------------------------------{----+
    +---------------------+
    """
    
    __queuePairs = {}
    __sendQueue = None
    __recvQueue = None

    def __init__(self):
        self.__sendQueue = Queue()
        self.__recvQueue = Queue()

    def newProcessQueuePair(self):
        label = str(uuid1())
        def regfunc(core2proc, proc2core, label):
            self.__queuePairs[label] = {\
                "pair": (core2proc, proc2core),
                "ok": True,
            }
        return ProcessQueuePair(regfunc, label)

    def process(self):
        possibleSender = []
        for label in self.__queuePairs:
            # healthy check
            if not self.__queuePairs[label]["ok"]: continue
            possibleSender.append(label)
            # try recv
            _, proc2core = self.__queuePairs[label]["pair"]
            while True:
                try:
                    got = proc2core.get_nowait()
                except Empty:
                    break
                except:
                    self.__queuePairs[label]["ok"] = False
                    break
                # try put received object to main recv queue
                try:
                    self.__recvQueue.put_nowait(got)
                except Full:
                    # do not try to receive more queues
                    return
        
        if len(possibleSender) < 1: return

        senderCount = len(possibleSender)
        while True:
            try:
                got = self.__sendQueue.get_nowait()
            except:
                break
            sender = possibleSender[random.randrange(0, senderCount)]
            core2proc, _ = self.__queuePairs[sender]["pair"]
            try:
                core2proc.put(got)
            except:
                continue

    def send(self, obj):
        """Send object to one of the processes randomly."""
        try:
            self.__sendQueue.put_nowait(obj)
        except Full:
            return False
        debug("1 Object put to main sending queue.")
        return True

    def recv(self):
        """Check for an object from anyone of the processes."""
        try:
            got = self.__recvQueue.get_nowait()
            debug("1 Object received from main receiving queue.")
            return got
        except Empty:
            return None
