#!/usr/bin/python3
# -*-python-*-

import json
import sys
from pprint import pprint

args = sys.argv
with open(args[1]) as data_file:    
    data = json.load(data_file)

pprint(data)
