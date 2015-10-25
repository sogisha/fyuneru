Fyuneru
=======

```
Currently under heavy development, documentation errors are not corrected.
Newest code will highly possible not work out-of-box.

当前正在进行大量的修改，文档错误也没有改正。
最新的代码很可能无法工作。
```

**向下拉动，见简体中文版本。**

**Fyuneru** lets you set up a server and a client computer within a virtual
ethernet, whose data frames over the virtual network cable are proxified
parallel via imagnative a lot of protocols. It also provides basical
encryption, which makes analyzing the traffic more difficult.

This software is licensed under GPLv2.



## Principle

Fyuneru ships with 2 parts: a core, and several proxies.

The **core** behaves on the server and client computer in an identical manner.
It first sets up the virtual network interface using Linux's TUN device and
deals with intercepting IP frames sending to and coming from it. When these
frames are leaving our computer, they are encrypted to ensure the 
confidentiality and integrity. It then listens for incoming connections on
several UDP ports.

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

### Dependencies

1. `python-pytun`, a python module used for setting up TUN devices. Use
   `sudo pip install python-pytun` to get this.
1. `salsa20`, a python module providing encryption for our program. Use
   `sudo pip install salsa20` to get this.
1. `xmpppy`, I've been using the one installed with:
     pip install git+https://github.com/ArchipelProject/xmpppy

## Usage

### Configuration

Install Fyuneru on both your server and your client. Before running, create a
file named `config.json` and place it in the same folder as the `run_as.py`.
Both server and client needs such a file, make sure they're **identical**.

An example of `config.json` is below.

```
{
    "version": "1.0",
    "core": {
        "server": {
            "ip": "10.1.0.1"
        },
        "client": {
            "ip": "10.1.0.2"
        },
        "key": "<USE A RANDOM AND LONG KEY TO REPLACE THIS>",
        "udpalloc": {
            "proxy-ss-01": {"server": 17100, "client": 7100}
        }
    },
    "proxies": {
        "proxy-ws-01": {
            "type": "websocket",
            "server": {
                "port": 7501 
            },
            "client": {
                "url": "ws://127.0.0.1/login/"
            }
        },
        "proxy-ss-01": {
            "type": "shadowsocks",
            "server": {
                "ip": "127.0.0.1",
                "port": 31000
            },
            "client": {
                "port": 10080
            }
        }
    }
}
```

Explanations to the configurations for the `core` section.

1. Set `core.server.ip` and `core.client.ip` as the desired virtual IP
   addresses for both computers.
1. `core.key` must be random and unique for your own security.
1. `core.udpalloc` defines interal UDP port allocations between proxy processes
   and core process.

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

Find the `run_as.py`, run `python run_as.py s` for setting up a server, and
`python run_as.py c` for setting up the client. You need root priviledge to
do this.

Add `--debug` after `run_as.py` will enable the debug mode(currently only for
the core). The IP frames will be dumped to the console.

---

Fyuneru
=======

**Scroll up for English version.**

**Fyuneru**允许您将服务器和客户端计算机用虚拟的以太网连接。
在虚拟的网线上传递的数据帧实际借助可以想象的一系列协议传送。
它同时提供基本的加密，使得分析流量更加困难。

本软件在GPLv2协议下进行许可。



## 原理

Fyuneru有两个部分：核心，和一系列代理。

**核心**在服务器和客户端计算机上运行时行为相同。
它首先使用Linux的TUN设备，建立一个虚拟的网卡。
之后，它就截获发往和来自这一网卡的IP数据帧。
这些数据帧在离开计算机之前会被加密，以确保其机密性和完整性。
之后，核心在多个UDP端口上监听，等待连接。

一旦在一个端口上由代理程序打通了UDP连接，这个端口就会被用来放出负载数据包：
即一部分加密的IP数据帧的。
至于对于特定的UDP端口，哪个IP数据帧会从这里释放出来，则是随机选择的。

**代理**负责双向传送UDP数据包。
代理会试图与服务器和客户机的UDP端口建立连接。
之后它使用自己的机制，不管是HTTP/AJAX/WebSocket还是XMPP或者别的什么来传送UDP包。
代理不一定和最终的服务器处于同一台计算机（
例如，您可以连接到XMPP服务器，然后将数据包发送到一个由最终的服务器所拥有的固定帐号上
）。

注意到服务器和客户机的行为是相同的：它为每个IP数据帧选择一个随机的代理。
这样对于上层的连接来说，具体的IP数据帧在请求和应答时都很有可能穿过不同的隧道，
协议和IP地址都可能不同。这种方式应当可以迷惑一个观察者——例如防火墙。


## 安装

### 系统要求

1. 操作系统：当前在Fedora 21和Ubuntu 14.04下测试完成。
1. 安装了Python2的环境。
1. 对于有些代理，需要使用NodeJS。

### 依赖的文件

1. `python-pytun`, 一个用来设定TUN设备的模块。
   使用命令`sudo pip install python-pytun`来安装这一模块。
1. `salsa20`，一个Python模块，为我们的程序提供加密服务。
   使用`sudo pip install salsa20`来安装这一模块。
1. `xmpppy`, 我使用如下命令安装：
    pip install git+https://github.com/ArchipelProject/xmpppy

## 用法

将Fyuneru安装在您的服务器和客户端上。运行前，创建一个叫做`config.json`的文件，
将它放在`run_as.py`相同的目录下。服务器和客户端都需要这样一个文件，
而且他们必须是**完全一样**的。

`config.json`的示例如下。

```
{
    "version": "1.0",
    "core": {
        "server": {
            "ip": "10.1.0.1"
        },
        "client": {
            "ip": "10.1.0.2"
        },
        "key": "<USE A RANDOM AND LONG KEY TO REPLACE THIS>",
        "udpalloc": {
            "proxy-ss-01": {"server": 17100, "client": 7100}
        }
    },
    "proxies": {
        "proxy-ws-01": {
            "type": "websocket",
            "server": {
                "port": 7501 
            },
            "client": {
                "url": "ws://127.0.0.1/login/"
            }
        },
        "proxy-ss-01": {
            "type": "shadowsocks",
            "server": {
                "ip": "127.0.0.1",
                "port": 31000
            },
            "client": {
                "port": 10080
            }
        }
    }
}
```

对`core`部分的解释：

1. 设置`core.server.ip`和`core.client.ip`为服务器和客户端所用的虚拟IP地址。
1. `core.key`必须是随机生成的、唯一的密钥（这对你的安全十分重要）。
1. `core.udpalloc`定义了用于核心进程和代理进程之间的UDP段口号分配。

为了配置具体的代理程序，要在`proxies`节中指定特定的参数。

#### 配置一个WebSocket代理

配置文件中需要有`proxies.websocket`的部分。

`proxies.websocket.server`包含3个键值：`ip`, `webport`, `coreports`。

1. `ip`是客户端用以连接服务器的地址。
2. `webport`是服务器所监听的、位于互联网的TCP端口。客户端将向这个端口发起连接。
3. `coreport`必须是`core.server.ports`的一个子集。
   在此指定哪些UDP端口将会被此代理所使用。

`proxies.websocket.client`包含一个键值：`coreports`。
它必须是`core.client.ports`的一个子集。

注意修改防火墙的设置，使得端口`proxies.websocket.server.webport`可以通过。

### 运行

找到`run_as.py`，用命令`python run_as.py s`来启动服务器。
用`python run_as.py c`来启动客户端。您需要提供root权限。

在`run_as.py`之后添加`--debug`标志将会进入调试模式（当前只能调试核心）。
在此模式下，将会在控制台输出收发的IP数据帧。
