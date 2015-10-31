import os

def proxyCommand(self, mode):
    proxyCommand = [
        'python',
        os.path.join(self.basepath, 'proxy.xmpp.py'),
        '--socket', self.proxyName, # proxy name used for socket channel
        '--uidname', self.user[0],
        '--gidname', self.user[1],
        '--parent-pid', str(self.pid),
    ]

    if mode == 's':
        proxyCommand += [
            '--peer', self.proxyConfig["client"]["jid"],
            '--jid', self.proxyConfig["server"]["jid"],
            '--password', self.proxyConfig["server"]["password"],
        ]
    else:
        proxyCommand += [
            '--peer', self.proxyConfig["server"]["jid"],
            '--jid', self.proxyConfig["client"]["jid"],
            '--password', self.proxyConfig["client"]["password"],
        ]
    
    return proxyCommand
