#!/usr/bin/python3 -i

# Handy utility to debug the bridge at the python command prompt.
# Bridge must be run in virtual-port mode.  

# hirsch@z87:~$ aconnect -o
# client 14: 'Midi Through' [type=kernel]
#    0 'Midi Through Port-0'
# client 130: 'RtMidiIn Client' [type=user]
#    0 'VIRT_PORT          '
#
# Given the above, open RtMidi as: 'RtMidi Input Client 128:0'

import sys
import mido
from time import sleep

mido.set_backend('mido.backends.rtmidi')

# Edit this as appropriate for your environment
virtual_port = 'RtMidiIn Client:VIRT_PORT 130:0'

def send( msg ):
    with mido.open_output(virtual_port) as outport:
        outport.send( msg )
        outport.close()
        
def capture( prog ):
    with mido.open_output(virtual_port) as outport:
        cc.control = 3
        cc.value = 127
        for i in range( 3 ):
            outport.send( cc )
            sleep( 0.2 )

        pc.program = prog
        outport.send( pc )
    outport.close()

pc = mido.Message('program_change')
cc = mido.Message('control_change')
sx = mido.Message('sysex')

pc.channel = 1
cc.channel = 1

# pc.program = #

# cc.control = 50
# cc.value = 64

# Set the various attributes at the python prompt and
# call send() - passing message object.
