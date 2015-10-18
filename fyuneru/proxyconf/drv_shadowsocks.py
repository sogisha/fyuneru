import hashlib
import hmac
import os


def proxyCommand(self, mode):
    sharedsecret= hmac.HMAC(\
        str(self.proxyName + '-shadowsocks'),
        self.baseKey,
        hashlib.sha256
    ).digest().encode('base64').strip()
    serverBinary = self.proxyConfig["server"]["bin"]
    clientBinary = self.proxyConfig["client"]["bin"]

    proxyCommand = [
        'python',
        os.path.join(self.basepath, 'proxy.shadowsocks.py'),
        '--uidname', self.user[0],
        '--gidname', self.user[1],
        '--socket', self.proxyName, # proxy name used for socket channel
        '-k', sharedsecret,
    ]

    if mode == 's':
        proxyCommand += [
            '--mode', 'server',
            '--bin', serverBinary,
            '-s', self.proxyConfig["server"]["ip"],
            '-p', str(self.proxyConfig["server"]["port"]),
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
        proxyCommand += [
            '--mode', 'client',
            '--bin', clientBinary,
            '-s', connectIP,
            '-p', str(connectPort),
            '-l', str(self.proxyConfig["client"]["port"]), # local tunnel entry 
        ]

    proxyCommand += [str(self.proxyConfig["server"]["forward-to"])]
    return proxyCommand
