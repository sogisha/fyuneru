#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import logging
from logging import info, debug, warning, error, critical, exception
import os
import signal
import sys
from select import select

from fyuneru.util.config import Configuration
from fyuneru.util.droproot import dropRoot
from fyuneru.vnet import VirtualNetworkInterface 
from fyuneru.proxies import ProxyProcesses


logging.basicConfig(level=logging.DEBUG)

PATH = os.path.realpath(os.path.dirname(sys.argv[0]))

##############################################################################

# required command line specification of role

if len(sys.argv) < 2 or sys.argv[1] not in ['s', 'c']:
    print "Usage: ./fyuneru.py {s|c}"
    sys.exit(1)

# record running role and report

mode = sys.argv[1]
if 's' == mode:
    info("Running in Server Mode.")
else:
    info("Running in Client Mode.")

# load configuration file 

config = Configuration(\
    mode,
    open(os.path.join(PATH, 'config.json'), 'r').read()
)

##############################################################################

proxies = ProxyProcesses()

# start virtual network interface and drop root

vnet = VirtualNetworkInterface(config.getCoreConfig())

# drop root

dropRoot(*config.user)

# start proxies

for each in config.listProxies():
    proxies.start(config.getProxyConfig(each))

# loop with vnet

proxies.distribute(vnet)

# exit loop

vnet.close()
