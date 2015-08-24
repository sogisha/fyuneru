Fyuneru
=======

**Fyuneru** lets you set up a server and a client computer within a virtual
ethernet, whose data frames over the virtual network cable are proxified
parallel via imagnative a lot of protocols. It also provides basical
encryption, which makes analyzing the traffic more difficult.

This software is licensed under GPLv2.



## Principle

Fyuneru ships with 2 parts: a core, and several proxies.

The **core** behaves on the server and client computer in an identical manner.
It first sets up the virtual network interface using Linux's TUN device and
deals with intercepting IP frames sending to and coming from it. These frames
are encrypted to ensure their confidentiality and integrity. It then it listens
for incoming connection on several UDP ports.

Once a UDP connection to a port, initiated by a proxy(described below), is
confirmed, this UDP port will be used for emitting the payload: a subset of the
encrypted IP frames. Which IP frame will be sent to a given UDP port, is
choosen randomly.

**Proxies** transmit bidirectional UDP packets. A proxy knocks both UDP ports
on the server and the client. It delivers the UDP packet using its own
mechanism, whatever HTTP/AJAX/WebSocket or XMPP or more. The proxy may also
not serves on the same server(e.g. you may connect a XMPP server, and send your
packet to a fixed account which is run by the proxy server).

Notice that the core on both server and client behaves the same: it chooses for
every IP frame a random proxy, therefore for a given connection or session, the
actual IP frame of request and response travels highly likely over different
routes with different protocols or even different IPs. This schema should
confuse an observer, e.g. a firewall.



## Installation

### System Requirements

1. Operating System: currently tested over Fedora 21 and Ubuntu 14.04;
1. Installed Python2 environment;
1. NodeJS is required by some proxies.

### Dependencies

#### Core

1. `python-pytun`, a python module used for setting up TUN devices. Use
   `sudo pip install python-pytun` to get this.
1. `salsa20`, a python module providing encryption for our program. Use
   `sudo pip install salsa20` to get this.

#### Proxies

For different proxies, you may need proxy-specific dependencies.

Following proxies are written in NodeJS. Install NodeJS, and run `npm install`
in the corresponding path to get dependencies installed.

1. `proxies/websocket`

## Usage

### Configuration

Install Fyuneru on both your server and your client. Before running, create a
file named `config.json` and place it in the same folder as the `run_as.py`.
Both server and client needs such a file, make sure they're **identical**.

An example of `config.json` is below. Do not remove any entry, just modify
their value if desired.

```
{
    "core": {
        "server": {
            "ip": "10.1.0.1",
            "ports": [17100,17101,17102,17103,17104]
        },
        "client": {
            "ip": "10.1.0.2",
            "ports": [7100,7101,7102,7103,7104]
        },
        "key": "<USE A RANDOM AND LONG KEY TO REPLACE THIS>"
    },
    "proxies": {
        "websocket": {
            "server": {
                "ip": "<ADDRESS OF THE SERVER RUNNING PROXY>",
                "webport": 6000,
                "coreports": [17100, 17101]
            },
            "client": {
                "coreports": [7100, 7101]
            }
        }
    }
}
```

Explanations to the configurations for the core.

1. Set `core.server.ip` and `core.client.ip` as the desired virtual IP
   addresses for both computers.
1. `core.server.ports` and `core.client.ports` are arrays containing a series
   of port numbers. They are the ports used by proxies.
1. Remeber to change `core.key` to a long key consists of random characters.
   This is cricital to your security.

To configure using a specific type of proxy, specify parameters in `proxies`
section.

#### Using WebSocket Proxy

Add section `proxies.websocket`.

`proxies.websocket.server` have 3 keys: `ip`, `webport`, `coreports`.

1. `ip` is the address of the server, which the client uses to connect.
2. `webport` is the TCP port the proxy server listens on. Client will connect
   to this port.
3. `coreport` must be a subset of `core.server.ports`. Specify which UDP ports
   of the core will be served by this proxy.

`proxies.websocket.client` have only one key: `coreports`. It has to be a
subset of `core.client.ports`.

Remember to configure the firewall on the server, to let
`proxies.websocket.server.webport` allowed.

### Run

Find the `run_as.py`, run `python run_as.py s` for setting up a server, 
