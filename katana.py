
import mido
import time
from time import sleep
import threading
import sys
from globals import *
import syslog

class Katana:

    def __init__( self, portname, channel, clear_input=False ):
        self.outport = mido.open_output( portname )
        self.inport = mido.open_input( portname )

        self.sysex = mido.Message('sysex')

        self.pc = mido.Message('program_change')
        self.pc.channel = channel

        self.cc = mido.Message('control_change')
        self.cc.channel = channel

        self.chunk_count = 0
        
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

    # Drain incoming USB buffer by doing polled reads over
    # five seconds
    def _clear_input( self ):
        # Force off edit mode
        # self.send_sysex_data( EDIT_OFF )
        start = time.time()
        while True:
            msg = self.inport.poll()
            now = time.time()
            if now - start > 5:
                break

    # Called by rtmidi in a separate thread to absorb bulk response
    def _post( self, msg ):
        if msg.type != 'sysex':
            syslog.syslog( "Err: Saw msg type: " + msg.type )

        self.receive_cond.acquire()

        curr_addr = msg.data[7:11]
        self.addr.append( curr_addr )

        curr_data = msg.data[11:-1]
        self.data.append( curr_data )

        # Signal the consumer if we've reached the expected number of messages.
        self.chunk_count += 1
        if self.chunk_count == self.target_count:
            self.chunk_count = 0
            self.receive_cond.notify()

        self.receive_cond.release()

    # Concatenate caller's prefix and message, add checksum and send
    # as sysex message. Handles both store and query commands.
    def _send( self, prefix, msg ):
        # print( "DEBUG: msg = ", msg )
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

    # Convenience method for store commands. Takes address and
    # optional data payload.
    def send_sysex_data( self, addr, data=None ):
        if data == None:
            msg = addr
        else:
            msg = list( addr )
            msg.extend( data )

        self._send( SEND_PREFIX, msg )

    # Encode scalar length into 4-byte sysex value
    @staticmethod
    def encode_scalar( len ):
        result = [0x00, 0x00, 0x00, 0x00]
        result[3] = len % 0x80
        result[2] = (len // 0x80) % 0x80
        result[1] = (len // 0x4000) % 0x80
        result[0] = (len // 0x200000) % 0x80
        return result

    @staticmethod
    def decode_array( ary ):
        return (ary[0] * 0x200000) + (ary[1] * 0x4000) + (ary[2] * 0x80) + ary[3]
    
    # Next (3) query methods return a two-element tuple in the general form:
    # [addrA, addrB, .. ], [ [dataA, .. ], [dataB, .. ], .. ]

    # For situations where we do not know the number of replies to be
    # expected. It appears that 5 seconds is enough time for Katana to
    # send a complete MIDI sysex dump.  Warning: If more data arrives 
    # after the timeout it will cause big problems when we attempt to
    # snapshot a preset.
    def get_bulk_sysex_data( self, msg, timeout=5 ):
        self.data = []
        self.addr = []

        self.target_count = 99
        self._send( QUERY_PREFIX, msg )
        sleep( timeout )
        return self.addr, self.data

    # Request sysex data by passing start address and length. This
    # method is generally for smaller, single-chunk messages.
    def query_sysex_data( self, addr, len ):
        self.receive_cond.acquire()

        self.data = []
        self.addr = []
        msg = list( addr )
        msg.extend( Katana.encode_scalar(len) )

        self.target_count = (len // 241) + 1
        self._send( QUERY_PREFIX, msg )

        result = self.receive_cond.wait(5)
        if not result:
            syslog.syslog( "Error: Timeout on cond wait" )

        self.receive_cond.release()

        return self.addr, self.data

    # Request sysex data (possibly requiring multiple chunks) by
    # passing first and last address of desired range. It is the
    # caller's responsibility to ensure the total response does not
    # span address discontinuities.  If that occurs the chunk count is
    # likely to be over-estimated and the operation will timeout.
    def query_sysex_range( self, first_addr, last_addr ):
        self.receive_cond.acquire()

        span = Katana.decode_array(last_addr) - Katana.decode_array(first_addr)
        offset = Katana.encode_scalar( span + 1 )
        
        self.data = []
        self.addr = []

        msg = list( first_addr )
        msg.extend( offset )

        # Calculate expected number of chunks.  Maximum chunk is 255 bytes
        # with max payload of 241 data bytes/
        self.target_count = ((span + 1) // 241) + 1
        self._send( QUERY_PREFIX, msg )
        result = self.receive_cond.wait(5)
        if not result:
            syslog.syslog( "Error: Timeout on cond wait" )

        self.receive_cond.release()

        return self.addr, self.data

    # Bias 4-byte sysex array by scalar value
    @staticmethod
    def effective_addr( base, offset ):
        base_scalar = Katana.decode_array( base )
        return Katana.encode_scalar( base_scalar + offset )
        
    # Request a single byte
    def query_sysex_byte( self, addr, offset=None ):
        if offset == None:
            eff = addr
        else:
            eff = Katana.effective_addr( addr, offset )

        (dummy, data) = self.query_sysex_data( eff, 1 )
        return data[0][0]
        
    # Send program change
    def send_pc( self, program ):
        self.pc.program = program
        self.outport.send( self.pc )

    # Send control change
    def send_cc( self, control, value ):
        self.cc.control = control
        self.cc.value = value
        self.outport.send( self.cc )

    # Convenience method to set amplifier volume
    def volume( self, value ):
        self.send_sysex_data( VOLUME_PEDAL_ADDR, (value,) )

    # Cycle volume pedal gain to provide audible signal
    def signal( self ):
        current_volume = self.query_sysex_byte( VOLUME_PEDAL_ADDR )

        for i in range(4):
            self.send_sysex_data( VOLUME_PEDAL_ADDR, (0,)  )
            sleep( 0.1 )
            self.send_sysex_data( VOLUME_PEDAL_ADDR, (50,) )

        self.send_sysex_data( VOLUME_PEDAL_ADDR, (current_volume,) )


if __name__ == '__main__':
    for test in (PANEL_STATE_ADDR, CURRENT_PRESET_ADDR):
        decode = Katana.decode_array( test )
        encode = Katana.encode_scalar( decode )
        test_list = list(test)
        if test_list != encode:
            print( "Failed:", test_list, "!=", encode )
