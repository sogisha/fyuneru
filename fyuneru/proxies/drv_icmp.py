import os

def proxyCommand(self, mode):
    proxyCommand = [
        'python',
        os.path.join(self.basepath, 'proxy.icmp.py'),
        '--socket', self.proxyName, # proxy name used for socket channel
        '--uidname', self.user[0],
        '--gidname', self.user[1],
        '--parent-pid', str(self.pid),
    ]

    if mode == 's':
        proxyCommand += [
            '--target', self.proxyConfig["client"]["ip"],
        ]
    else:
        proxyCommand += [
            '--target', self.proxyConfig["server"]["ip"],
        ]
    
    return proxyCommand
