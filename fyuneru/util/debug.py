import socket
from struct import * 
import logging
import sys
import os

##############################################################################

def configLoggingModule(debug):
    logLevel = logging.INFO
    if debug: logLevel = logging.DEBUG

    procname = os.path.basename(sys.argv[0])
    logFormat = \
        "\n=== [%%(asctime)-15s] [%s]: %%(levelname)s\n %%(message)s"\
        % procname 
    

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

def _decodeIPFrame(buf):
    ip_header = buf[0:20]
    iph = unpack('!BBHHHBBH4s4s' , ip_header)
     
    version_ihl = iph[0]
    version = (version_ihl >> 4) & 0xF
    ihl = version_ihl & 0xF
     
    iph_length = ihl * 4
     
    ttl = iph[5]
    protocol = iph[6]
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])

    payload = buf[iph_length:]

    ip_meta = {
        "version": version,
        "length": str(ihl),
        "TTL": ttl,
        "protocol": protocol,
        "src": str(s_addr),
        "dst": str(d_addr),
    }
    return ip_meta, payload

def showPacket(buf):
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
        start += len(line)
        hexstr = hexstr.ljust(3 * width)
        ret += "%08x: %s: %s\n" % (start, hexstr, asciistr)

    ipReport = ''
    try:
        ipMeta, ipPayload = _decodeIPFrame(origbuf)
        ipReport = "Ver %s :: TTL %d :: Protocol %s :: Src %s :: Dst %s" % (\
            ipMeta["version"],
            ipMeta["TTL"],
            ipMeta["protocol"],
            ipMeta["src"],
            ipMeta["dst"]
        )
        ret = ipReport + "\n" + ret
    except Exception,e:
        print e
        pass

    return ret.strip() 

##############################################################################

if __name__ == '__main__':
    import os
    print showPacket(os.urandom(200))
