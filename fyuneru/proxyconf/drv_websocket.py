import os

def proxyCommand(self, mode):
    proxyCommand = ['node']
    if mode == 's':
        proxyCommand += [
            os.path.join(self.proxyBase, 'websocket', 'server.js'),
            str(self.proxyConfig["server"]["port"]),
        ]
        proxyCommand.append(str(self.portServer))
    else:
        proxyCommand += [
            os.path.join(self.proxyBase, 'websocket', 'client.js'),
            self.proxyConfig["client"]["url"],
        ]
        proxyCommand.append(str(self.portClient))
    return proxyCommand
