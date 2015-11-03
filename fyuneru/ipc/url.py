"""
URL for starting IPC client
===========================

This tells the IPC client how to find the IPC server, do authentication
and identify itself to server.
"""

_URLPREFIX = "fyuneru-ipc://"

class InvalidIPCServerURLException(Exception): pass

class IPCServerURL:

    host = "127.0.0.1"
    port = 64089
    key = ""
    user = ""
    
    def __init__(self, url=None):
        if None == url: return
        try:
            if not url.startswith(_URLPREFIX): raise
            url = url[len(_URLPREFIX):]
            split = url.replace('@', ':').split(':')
            user, key, host, port = split
            user = user.decode('hex')
            key = key.decode('hex')
            port = int(port)
            if not port in xrange(0, 65536): raise
            self.host, self.port, self.key, self.user = host, port, key, user
        except:
            raise InvalidIPCServerURLException()

    def __str__(self):
        user = self.user.encode('hex')
        key = self.key.encode('hex')
        return _URLPREFIX + ("%s:%s@%s:%d" % (user, key, self.host, self.port))


if __name__ == "__main__":
    url = IPCServerURL()
    url.key = 'kadsjfakl'
    url.user = 'proxy1'
    print str(url)

    url2 = IPCServerURL(str(url))
    print url2.host, url2.port, url2.key, url2.user
