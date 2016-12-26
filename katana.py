
import mido
import time
from time import sleep
import threading
import sys
from globals import *

class Katana:

    def __init__( self, portname, channel, clear_input=False ):
        self.outport = mido.open_output( portname )
        self.inport = mido.open_input( portname )

        self.sysex = mido.Message('sysex')

        self.pc = mido.Message('program_change')
        self.pc.channel = channel

        self.cc = mido.Message('control_change')
        self.cc.channel = channel

        # Thread synchronization around incoming MIDI data. Used only
        # in the case where a single message is expected.  We need to use
        # a different approach for bulk sysex dumps where an arbitrary 
        # number of replies may be sent.
        self.receive_cond = threading.Condition()
        self.addr = []
        self.data = []

        if clear_input: 
            self._clear_input()

        # Since mido callbacks take only a single parameter, bind
        # the current object into a closure
        self.inport.callback = lambda msg: self._post( msg )

    # Drain incoming USB buffer
    def _clear_input( self ):
        # Force off edit mode
        self.set_sysex_data( EDIT_OFF )
        start = time.time()
        while True:
            msg = self.inport.poll()
            now = time.time()
            if now - start > 5:
                break

    # Called by rtmidi in a separate thread
    def _post( self, msg ):
        if msg.type != 'sysex':
            print( "Err: Saw msg type: " + msg.type )
            sys.exit( 1 )

        self.receive_cond.acquire()

        curr_addr = msg.data[7:11]
        self.addr.append( curr_addr )

        curr_data = msg.data[11:-1]
        self.data.append( curr_data )

        self.receive_cond.notify()
        self.receive_cond.release()

    def _send( self, prefix, msg ):
        # Calculate Roland cksum on msg only
        accum = 0
        for byte in msg:
            accum = (accum + byte) & 0x7f
            cksum = (0x80 - accum) & 0x7f

        data = []
        data.extend( prefix )
        data.extend( msg )
        data.append( cksum )
        self.sysex.data = data
        self.outport.send( self.sysex )

    def set_sysex_data( self, msg ):
        self._send( SEND_PREFIX, msg )

    # Return a tuple of [addr1, addr2, .. , addrN], [ [d1a, .. d1X], [d2a, ,, d2X], .. [dNa, .. dNX] ]

    # For situations where we do not know the number of replies to be
    # expected. It appears that 5 seconds is enough time for Katana to
    # send a complete MIDI sysex dump.  Warning: If more data arrives 
    # after the timeout it will cause big problems when we attempt to
    # snapshot a preset.  The query for current preset will get any
    # garbage that was left over and could freeze.
    def get_bulk_sysex_data( self, msg, timeout=5 ):
        self.data = []
        self.addr = []

        self._send( QUERY_PREFIX, msg )
        sleep( timeout )
        return self.addr, self.data

    def get_sysex_data( self, msg ):
        self.receive_cond.acquire()

        self.data = []
        self.addr = []
        self._send( QUERY_PREFIX, msg )

        result = self.receive_cond.wait(5)
        if not result:
            print( "Error: Timeout on cond wait" )
            sys.exit( 1 )

        self.receive_cond.release()

        return self.addr, self.data

    def send_fast_pc( self, program ):
        # Normalize to behave like PC
        if program == 4: 
            program = 0
        else: 
            program += 1

        # Enter edit mode
        self.set_sysex_data( EDIT_ON )
        preset_cmd = CURRENT_PRESET_ADDR[:]
        preset_cmd.extend( [0x00, program] )
        self.set_sysex_data( preset_cmd )
        # Leave edit mode
        self.set_sysex_data( EDIT_OFF )

    def send_pc( self, program ):
        self.pc.program = program
        self.outport.send( self.pc )

    def send_cc( self, control, value ):
        self.cc.control = control
        self.cc.value = value
        self.outport.send( self.cc )

    def volume( self, value ):
        cmd = AMP_VOLUME_ADDR[:]
        if value > 0: value += 1
        cmd.append( int(value/2) )
        self.set_sysex_data( cmd )

    # Cycle amp-type LEDs in a distinctive pattern
    def signal( self ):
        # Get type, gain, volume
        cmd = AMP_TYPE_ADDR[:]
        cmd.extend( [0x00, 0x00, 0x00, 0x03] )
        addr, curr = self.get_sysex_data( cmd )

        # Zero out gain and volume while cycling
        # the amp-type LEDs
        cmd = AMP_TYPE_ADDR[:]
        cmd.extend( [0x00, 0x00, 0x00] )
        vals = (0, 2, 4, 2)
        for i in range(4):
            cmd[4] = vals[ i % 3 ]
            self.set_sysex_data( cmd )
            sleep( 0.6 )

        # Restore type, gain, volume
        cmd = AMP_TYPE_ADDR[:]
        cmd.extend( curr[0] )
        self.set_sysex_data( cmd )
