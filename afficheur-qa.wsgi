#!/usr/bin/python3

import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/home/jv/afficheur-qa/realtime-data-with-map")

from monitor import app as application
