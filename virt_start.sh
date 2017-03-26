#!/bin/bash

# For testing.  Starts bridge on a virtual port so test 
# program can connect.

./katana_bridge_app \
    VIRT_PORT 2 \
    "KATANA:KATANA MIDI 1 20:0" 1 \
    test.file \
    virt
