#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import logging
from logging import info, debug, warning, error, critical
import os
import signal
import sys

from fyuneru.util.config import Configuration
from fyuneru.util.droproot import dropRoot
from fyuneru.vnet import start as startVNet


logging.basicConfig(level=logging.INFO)

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

vnetPipe, vnetProc = startVNet(config.getCoreConfig())

