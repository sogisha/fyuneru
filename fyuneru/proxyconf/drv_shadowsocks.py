import hashlib
import hmac
import os


def proxyCommand(self, mode):
    sharedsecret= hmac.HMAC(\
        'shadowsocks',
        self.baseKey,
        hashlib.sha256
    ).digest().encode('base64').strip()
    serverBinary = self.proxyConfig["server"]["bin"]
    clientBinary = self.proxyConfig["client"]["bin"]

    if mode == 's':
        # TODO we used now here at server a direct ss-tunnel. This has to
        # be modified, since at server there is UNIX socket instead of port
        # number
        proxyCommand = [
            serverBinary,
            '-k', sharedsecret,
            '-m', 'aes-256-cfb',
            '-s', self.proxyConfig["server"]["ip"],
            '-p', str(self.proxyConfig["server"]["port"]),
            '-U',
        ]
    else:
        # 1. packet will be locally sent to client.ip:client.port
        # 2. packet is then proxified through ss-tunnel.
        # 3. `ss-tunnel` is however not always connected directly to server.
        #    If a intermediate server exists with port-forwarding, it can be
        #    configured to connect to this fake-port.
        # 4. packet is always emitted at ss-tunnel's server and forwared to
        #    127.0.0.1:port.server(UDP) at server side.
        if self.proxyConfig["client"].has_key("proxy"):
            connectIP = self.proxyConfig["client"]["proxy"]["ip"]
            connectPort = self.proxyConfig["client"]["proxy"]["port"]
        else:
            connectIP = self.proxyConfig["server"]["ip"]
            connectPort = self.proxyConfig["server"]["port"]

        proxyCommand = [
            'python',
            os.path.join(self.proxyBase, 'shadowsocks', 'client.py'),
            '--bin', clientBinary,
            '-k', sharedsecret,
            '-s', connectIP,
            '-p', str(connectPort),
            '-b', '127.0.0.1', # listens on local ip
            '-l', str(self.proxyConfig["client"]["port"]),
            '-m', 'aes-256-cfb',
            str(self.proxySocket),        # local internal UNIX socket path
            connectIP,
            str(connectPort),
        ]
    return proxyCommand
