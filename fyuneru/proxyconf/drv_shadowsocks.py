import hashlib
import hmac
import os


def proxyCommand(self, mode):
    sharedsecret= hmac.HMAC(\
        'shadowsocks',
        self.baseKey,
        hashlib.sha256
    ).digest().encode('base64').strip()
    serverBinary = self.proxyConfig["tunnel"]["binary"]["server"]
    clientBinary = self.proxyConfig["tunnel"]["binary"]["client"]

    if mode == 's':
        proxyCommand = [
            serverBinary,
            '-k', sharedsecret,
            '-m', 'aes-256-cfb',
            '-s', self.proxyConfig["tunnel"]["server"]["ip"],
            '-p', str(self.proxyConfig["tunnel"]["server"]["port"]),
            '-U',
        ]
    else:
        proxyCommand = [
            'python',
            os.path.join(self.proxyBase, 'shadowsocks', 'client.py'),
            '--bin', clientBinary,
            '-k', sharedsecret,
            '-s', self.proxyConfig["tunnel"]["server"]["ip"],
            '-p', str(self.proxyConfig["tunnel"]["server"]["port"]),
            '-b', self.proxyConfig["tunnel"]["client"]["ip"],
            '-l', str(self.proxyConfig["tunnel"]["client"]["port"]),
            '-m', 'aes-256-cfb',
            str(self.portClient),         # local  udp listening port
            self.proxyConfig["entrance"], # remote udp listening addr
            str(self.portServer),         # remote udp listening port
        ]
    return proxyCommand
