import logging
import sys
import os

from ..net.protocol import IPPacket

##############################################################################

def configLoggingModule(debug):
    logLevel = logging.INFO
    if debug: logLevel = logging.DEBUG

    procname = os.path.basename(sys.argv[0])
    logFormat = \
        "\n=== [%%(asctime)-15s] [%s|%d]: %%(levelname)s\n %%(message)s"\
        % (procname, os.getpid())
    

    logging.basicConfig(\
        level=logLevel,
        format=logFormat
    )

##############################################################################

def colorify(text, color):
    colors = {\
        "blue": '\033[94m',
        "green": '\033[92m',
        "red": '\033[91m',
    }
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    return colors[color] + text + ENDC

##############################################################################

def showPacket(p):
    if type(p) == str:
        buf = p
        p = IPPacket(p)
    elif isinstance(p, IPPacket):
        buf = str(p)
    else:
        return '(Not a valid IP packet)'
    
    width = 16
    lines = []
    origbuf = buf 
    while buf != '':
        lines.append(buf[:width])
        buf = buf[width:]
    ret = ''
    start = 0
    for line in lines:
        hexstr = ''
        asciistr = ''
        for c in line:
            ordc = ord(c)
            hexstr += '%02x ' % ordc
            if ordc <= 0x7E and ordc >= 0x20:
                asciistr += c
            else:
                asciistr += '.'
        hexstr = hexstr.ljust(3 * width)
        ret += "%08x: %s: %s\n" % (start, hexstr, asciistr)
        start += len(line)

    ipReport = ''
    try:
        ipReport = "Ver %s :: TTL %d :: Protocol %s(%s) :: Src %s :: Dst %s" % (\
            p.version,
            p.TTL,
            p.protocol, p.protocolName,
            p.src,
            p.dst
        )
        ret = ipReport + "\n" + ret
    except Exception,e:
        print e
        pass

    return ret.strip() 

def showIPCReport(buf):
    return ''

##############################################################################

if __name__ == '__main__':
    import os
    print showPacket(os.urandom(200))
