"""
Provides several tools for connecting core process and proxy process using
queues in multiprocessing module.
"""

import multiprocessing

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
           |   |          +--------->-------| PROXY 01   QC.proc[1].recv |
           |   |          |                 |            QC.proc[1].send |>-+
           |   |          |                 +----------------------------+  |
           |   |          ^       ... +--->--------------------------------+|
           |   |          |  |  |     |     +----------------------------+ ||
           |   |        +----------------+  | PROXY 02  QC.proc[2].recv  |<+|
           |   |        | Random Routing |  |           QC.proc[2].send  |>+|
          \|/  |        +----------------+  +----------------------------+ ||
                                |                                          ||
    +---------------------+     |                                          ||
    | CORE  QC.core.send  |-->--+                                       ___||
    |       QC.core.recv  |--<-----------------------------------------{----+
    +---------------------+
    """
