Fyuneru v1.1
============


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
confidentiality and integrity.

The core communicates with serveral proxies using UNIX Sockets in UDP
Datagrams, which are also managed by Fyuneru. The proxies are choosen randomly
to receive encrypted packets from the core. Then, how the proxies send these
packets, varies. 

Currently we have officially written 2 proxies by using Shadowsocks and XMPP
protocol. Shadowsocks sends UDP packets using an encrypted connection directly
to a server with little protocol footprint, and XMPP sends our packets using
TCP via up to 2 intermediate servers. You may configure Fyuneru to initiate
several such proxies, making a lot of proxy paths.

Notice that the core on both server and client behaves the same: it chooses for
every IP frame a random proxy, therefore for a given connection or session, the
actual IP frame of request and response travels highly likely over different
routes with different protocols and even different IPs(in case of XMPP, etc).
This schema should confuse an observer, e.g. a firewall.



## Installation

### System Requirements

1. Operating System: currently tested over Fedora 21 and Ubuntu 14.04;
1. Installed Python2 environment;
1. Dependencies installed, see below.

### Dependencies

1. `salsa20`, a python module providing encryption for our program. Use
   `sudo pip install salsa20` to get this.
2. `xmpppy`, if you want to use XMPP proxies. I have forked an library on
   github at <https://github.com/sogisha/xmpppy>, follow the instructions
   to get it installed.
3. `shadowsocks-libev`, you are likely to compile it on your self. I have also
   forked one at <https://github.com/sogisha/shadowsocks-libev>, follow the
   instructions to compile it and install.

## Usage

### Add user and group for Fyuneru

You have to set up your system with an user and a group, in which Fyuneru
will run. Recommended is `nobody` for both.

### Configuration

Install Fyuneru on both your server and your client. Before running, create a
file named `config.json` and place it in the same folder as the `run_as.py`.
Both server and client needs such a file, make sure they're **identical**.

An example of `config.json` is below. Read instructions below to get
explanations!

```
{
    "version": "1.1",
    "core": {
        "server": {
            "ip": "10.1.0.1"
        },
        "client": {
            "ip": "10.1.0.2"
        },
        "user": {
            "uidname": "nobody",
            "gidname": "nobody"
        },
        "key": "DEVELOPMENT ONLY"
    },
    "proxies": {
        "proxy-ss-01": {
            "type": "shadowsocks",
            "server": {
                "bin": "/usr/local/bin/ss-server",
                "ip": "<SERVER-IP>",
                "port": 31000,
                "forward-to": 10081
            },
            "client": {
                "bin": "/usr/local/bin/ss-tunnel",
                "port": 10080,
                "proxy": {
                    "ip": "<PROXY-IP>",
                    "port": 31000
                }
            }
        },
        "proxy-xmpp-01": {
            "type": "xmpp",
            "server": {
                "jid": "jid1@test.com",
                "password": "jid1_password"
            },
            "client": {
                "jid": "jid2@example.com",
                "password": "jid2_password"
            }
        }
    }
}
```

#### Section `core`

1. Set `core.server.ip` and `core.client.ip` as the desired virtual IP
   addresses for both computers.
1. `core.key` must be random and unique for your own security.
1. `core.user.uidname` and `core.user.gidname` are UID/GID allocated to
   Fyuneru. After setting up necessary network devices, Fyuneru will jump
   to this UID/GID and give up root privileges.

#### Section `proxies`

To configure using a specific type of proxy, specify parameters in `proxies`
section.

You have to give each proxy a name. `proxy-ss-01` or `proxy-xmpp-01` are
examples. They are going to appear in the log output.

##### To add a Shadowsocks proxy

You have to write the section of a proxy like this:

```
"<PROXY-NAME>": {
    "type": "shadowsocks",
    "server": {
        "bin": "/usr/local/bin/ss-server",
        "ip": "<SERVER-IP>",
        "port": 31000,
        "forward-to": 10081
    },
    "client": {
        "bin": "/usr/local/bin/ss-tunnel",
        "port": 10080,
        "proxy": {
            "ip": "<PROXY-IP>",
            "port": 31000
        }
    }
}
```

1. `type` must be `shadowsocks` to tell the program start a Shadowsocks proxy.
1. `server.bin` points to the `ss-server` binary, and `client.bin` to the
   `ss-tunnel` binary.
2. `server.ip` and `server.port` are IP and port, on which the server should
   listen in Internet.
3. `server.forward-to` is the port used by the server-side adapter of Fyuneru.
   Choose it as you like. Similarily is `client.port` the port used by the
   client-side adapter of Fyuneru.
4. `client.proxy` is optional. If you want to ask the client to connect to a
   port-forwarded server, not directly to the server port, use this. Otherwise
   we'll just connect to `server.ip`:`server.port` directly.

##### To add a XMPP proxy

```
"<PROXY-NAME>": {
    "type": "xmpp",
    "server": {
        "jid": "jid1@test.com",
        "password": "jid1_password"
    },
    "client": {
        "jid": "jid2@example.com",
        "password": "jid2_password"
    }
}
```

1. `type` must be `xmpp` to tell the program start a XMPP proxy.
2. Both server and client requires the same format, providing a `jid` and
   a `password`. You have to apply for 2 XMPP accounts(they don't have to be
   from the same service provider, but the client account's provider should be
   reachable from your Internet environment).

### Run

Find the `run_as.py`, run `python run_as.py s` for setting up a server, and
`python run_as.py c` for setting up the client. You need root priviledge to
do this.

Add `--debug` after `run_as.py` will enable the debug mode. The IP frames will
be dumped to the console.

---

Fyuneru
=======

**Scroll up for English version.**

**Fyuneru**允许您将服务器和客户端计算机用虚拟的以太网连接。
在虚拟的网线上传递的数据帧实际借助可以想象的一系列协议传送。
它同时提供基本的加密，使得分析流量更加困难。

本软件在GPLv2协议下进行许可。




## 原理

Fyuneru包含两个部分：核心，和一系列代理。

**核心**在服务器和客户端上的行为是相同的。
它首先使用Linux的TUN设备建立一个虚拟网卡，然后收发这个网卡上的IP数据帧。
这些数据帧离开我们的计算机之前会被加密，以便保证它们的机密性和完整性。

核心使用Unix Socket和各个代理之间使用UDP数据包通信。这些代理也是Fyuneru管理的。
核心随机地向代理发送数据包，之后，代理用自己的不同方式将这些数据包发到服务器。

当前我们提供2种代理：利用Shadowsocks和XMPP协议的。
Shadowsocks使用一种难以分析特征的协议向服务器直接发出UDP数据包，
XMPP将数据包通过TCP连接传递，但利用了最多2个中间服务器。
您可以配置Fyuneru启动多个这样的代理进程，以便设定多个代理路径。

注意到，服务器和客户端的核心有相同的行为：对每个IP数据帧，它都随机选择一个代理。
即使是对于同样的连接会话，实际上的IP数据帧也是通过不同的路径、不同的协议甚至不同的IP传递的（例如XMPP协议）。
这种方式可以扰乱例如防火墙这样的观察者。



## 安装

### 系统需求

1. 操作系统：当前在Fedora 21和Ubuntu 14.04上进行了测试。
1. 需要有Python2的环境。
1. 需要安装如下所述的依赖包。

### 依赖包

1. `salsa20`, 为我们的程序提供加密的Python模块。使用如下命令安装：
   `sudo pip install salsa20`
2. `xmpppy`, 如果要使用XMPP代理的话。可以从我在github上fork的地址找到：
   <https://github.com/sogisha/xmpppy>，按照上面的指示安装。
3. `shadowsocks-libev`, 您可能需要自己编译安装。我在github上也fork了一份：
   <https://github.com/sogisha/shadowsocks-libev>，同样按照上面的指示编译安装。



## 用法 

### 添加Fyuneru使用的用户和组

您需要在系统中添加一个用户和一个组，Fyuneru将以它们的身份运行。
推荐用`nobody`作为用户和组。

### 配置

您需要在服务器和客户端上都安装Fyuneru。在运行前，创建一个`config.json`文件，
将其放在和`run_as.py`同样的目录下。
服务器和客户端都需要这样一个文件，且请确认它们完全一致。

`config.json`的内容类似如下，请根据后文的指示具体配置。

```
{
    "version": "1.1",
    "core": {
        "server": {
            "ip": "10.1.0.1"
        },
        "client": {
            "ip": "10.1.0.2"
        },
        "user": {
            "uidname": "nobody",
            "gidname": "nobody"
        },
        "key": "DEVELOPMENT ONLY"
    },
    "proxies": {
        "proxy-ss-01": {
            "type": "shadowsocks",
            "server": {
                "bin": "/usr/local/bin/ss-server",
                "ip": "<SERVER-IP>",
                "port": 31000,
                "forward-to": 10081
            },
            "client": {
                "bin": "/usr/local/bin/ss-tunnel",
                "port": 10080,
                "proxy": {
                    "ip": "<PROXY-IP>",
                    "port": 31000
                }
            }
        },
        "proxy-xmpp-01": {
            "type": "xmpp",
            "server": {
                "jid": "jid1@test.com",
                "password": "jid1_password"
            },
            "client": {
                "jid": "jid2@example.com",
                "password": "jid2_password"
            }
        }
    }
}
```

#### `core`部分

1. 将`core.server.ip`和`core.client.ip`设定为服务器和客户端的虚拟IP地址。
1. `core.key`必须是一个随机的密钥，这是为了您的安全着想。
1. `core.user.uidname`和`core.user.gidname`是分配给Fyuneru使用的UID/GID。
   在设定了虚拟网卡等设备后，Fyuneru将会以这个身份运行，放弃root权限。

#### `proxies`部分

为了配置某个代理，需要在`proxies`部分中增加对应的内容。

您需要给每个代理取一个名字，例如示例中的`proxy-ss-01`或`proxy-xmpp-01`。
它们会出现在日志中。

##### 要添加一个Shadowsocks代理

您需要将代理部分的配置写成类似如下的形式：

```
"<PROXY-NAME>": {
    "type": "shadowsocks",
    "server": {
        "bin": "/usr/local/bin/ss-server",
        "ip": "<SERVER-IP>",
        "port": 31000,
        "forward-to": 10081
    },
    "client": {
        "bin": "/usr/local/bin/ss-tunnel",
        "port": 10080,
        "proxy": {
            "ip": "<PROXY-IP>",
            "port": 31000
        }
    }
}
```

1. `type`必须是`shadowsocks`，这样程序就会启动一个Shadowsocks代理。
1. `server.bin`指向`ss-server`这个程序的二进制文件，`client.bin`指向`ss-tunnel`的二进制文件。
2. `server.ip`和`server.port`是服务器在互联网上监听所用的IP地址和端口号。
3. `server.forward-to`是服务器端Fyuneru的代理程序所用的内部端口号。
   按照您想要的数字选择。
   同样地，`client.port`是客户端Fyuneru代理程序所用的端口号。
4. `client.proxy`是可选的。如果您为Shadowsocks设定了一个端口转发，
   可以用这个方式让客户端连接到被转发的IP地址和端口上。
   如果您不指定，将会使用由`server.ip`:`server.port`确定的目标地址。

##### 要添加一个XMPP代理

```
"<PROXY-NAME>": {
    "type": "xmpp",
    "server": {
        "jid": "jid1@test.com",
        "password": "jid1_password"
    },
    "client": {
        "jid": "jid2@example.com",
        "password": "jid2_password"
    }
}
```

1. `type`必须是`xmpp`，这样程序会启动一个XMPP代理。
2. 服务器和客户端都需要同样形式的配置：`jid`和`password`。
   您需要申请2个XMPP帐号（他们不一定来自同一个服务提供商，
   但客户端所用的帐号所在的服务器应当能在您的互联网环境中可以直接访问）。

### 运行

找到`run_as.py`，用命令`python run_as.py s`来启动服务器。
用`python run_as.py c`来启动客户端。您需要提供root权限。

在`run_as.py`之后添加`--debug`标志将会进入调试模式。
在此模式下，将会在控制台输出收发的IP数据帧。
