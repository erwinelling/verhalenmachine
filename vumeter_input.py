#!/usr/bin/env python
import os
import sys
import logging, logging.handlers

HOME_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(HOME_DIR, "vumeter_input.log")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.handlers.RotatingFileHandler(
              LOG_FILE, maxBytes=5000000, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


import fileinput

for line in fileinput.input():
    logger.debug(line)
    print "hoi"

# data = sys.stdin.read()
# hello(data)
