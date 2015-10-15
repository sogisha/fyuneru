import hashlib
import hmac
import os


def proxyCommand(self, mode):
    sharedsecret= hmac.HMAC(\
        'shadowsocks',
        self.baseKey,
        hashlib.sha256
    ).digest().encode('base64').strip()
    serverBinary = self.proxyConfig["tunnel-server"]["bin"]
    clientBinary = self.proxyConfig["tunnel-client"]["bin"]

    if mode == 's':
        proxyCommand = [
            serverBinary,
            '-k', sharedsecret,
            '-m', 'aes-256-cfb',
            '-s', self.proxyConfig["tunnel-server"]["ip"],
            '-p', str(self.proxyConfig["tunnel-client"]["port"]),
            '-U',
        ]
    else:
        proxyCommand = [
            'python',
            os.path.join(self.proxyBase, 'shadowsocks', 'client.py'),
            '--bin', clientBinary,
            '-k', sharedsecret,
            '-s', self.proxyConfig["tunnel-server"]["ip"],
            '-p', str(self.proxyConfig["tunnel-server"]["port"]),
            '-b', '127.0.0.1',
            '-l', str(self.proxyConfig["tunnel-client"]["port"]),
            '-m', 'aes-256-cfb',
            str(self.portClient),       # local  udp listening port
            self.proxyConfig["server"], # remote udp listening addr
            str(self.portServer),       # remote udp listening port
        ]
    return proxyCommand
