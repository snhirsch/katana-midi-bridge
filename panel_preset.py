#!/usr/bin/python3
#
# Represent a preset 
#
#

import sys
import re
from time import sleep
from globals import *


class PanelPreset:

    # Track object state
    Start, SawId, SawCh, SawAddr, SawData, Done = range( 6 )

    # Static generator to create multiple PanelPreset objects by parsing a
    # text file input stream
    #
    @staticmethod
    def get_from_file( infh ):
        lineNum = 0
        obj = PanelPreset(None, None, None)
        for line in infh:
            lineNum += 1
            line = line.strip()
            if len( line ) == 0: continue
            if re.match( r'^#', line ): continue

            try:
                type, value = line.split( ' ', 1 )
            except ValueError:
                print( "Parse error at line %d. Expected more than one token." % lineNum )
                sys.exit( 1 )

            # First token in input line names the handler.  
            handler = getattr( obj, type, None )
            if handler == None:
                print( "Parse error at line %d. Line type %s unknown" % (lineNum, type) )
                sys.exit( 1 )
            else:
                handler( value, lineNum )

            if obj.state == obj.Done:
                obj.volume_midi_scale = obj.get_data(PANEL_STATE_ADDR, 2, 1)[0] / 128
                yield obj
                obj = PanelPreset(None, None, None)
                
        if obj.state != obj.Start:
            print( "Parse error at line %d." % lineNum )

    # Static factory method to create a single PanelPreset object by reading
    # current amplifier state
    #
    @staticmethod
    def read_from_amp( katana, preset_id, colorObj, simpleObj, complexObj ):
        obj = PanelPreset( colorObj, simpleObj, complexObj )
        obj.state = obj.Done
        obj.id = preset_id

        # NOTE: This code can hang or blow up with invalid list index if
        #       remnants from an earlier reply are sitting in the input
        #       buffer.

        # # Enter edit mode
        # katana.send_sysex_data( EDIT_ON )
        # # Must give it settling time
        # sleep( 0.1 )
        # dummy, preset = katana.query_sysex_data( CURRENT_PRESET_ADDR, CURRENT_PRESET_LEN )
        
        # # Leave edit mode
        # katana.send_sysex_data( EDIT_OFF )
        # obj.ch = preset[0][1]

        # # Normalize low-level preset id to the one presented on public
        # # PC implementation
        # obj.ch -= 1
        # if obj.ch < 0: obj.ch = 4

        # Read active DSP deep parms
        for rec in colorObj.read_color_assign( katana ):
            # Get the appropriate group handler
            handler = obj.dsp[ rec['group'] ]
            # Lookup parm blocks
            coords = handler.get_coords( rec['category'], rec['type'] )
            # And read from amp
            for block in coords['blocks']:
                addr, length = block
                addr, data = katana.query_sysex_data( addr, length )
                obj.addr.append( addr[0] )
                obj.data.append( data[0] )
                obj.memo.append( "Category: %s, Type: %s" % (rec['category'], coords['name']) )
        
        # Read color assign and state
        addr, data = katana.query_sysex_data( COLOR_ASSIGN_ADDR, COLOR_ASSIGN_LEN )
        obj.addr.append( addr[0] )
        obj.data.append( data[0] )
        obj.memo.append( "Color Assign" )
        
        # Read amplifier panel block
        addr, data = katana.query_sysex_data( PANEL_STATE_ADDR, PANEL_STATE_LEN )
        obj.addr.append( addr[0] )
        obj.data.append( data[0] )
        obj.memo.append( "Amp Panel" )
        
        # Read noise gate state
        addr, data = katana.query_sysex_data( NS_ADDR, NS_LEN )
        obj.addr.append( addr[0] )
        obj.data.append( data[0] )
        obj.memo.append( "Noise Gate" )
        
        # Keep this around so we can properly scale controller
        # pedal input
        obj.volume_midi_scale = data[0][2] / 128
        
        return obj

    def __init__( self, colorObj, simpleObj, complexObj ):
        self.state = self.Start
        self.id = -1
        self.ch = -1
        self.addr = []
        self.data = []
        self.memo = []
        self.by_addr = {}
        self.curr_address = None
        self.colorObj = colorObj
        self.dsp = {}
        self.dsp['simple'] = simpleObj
        self.dsp['complex'] = complexObj

    # State machine handlers for parsing data file:
        
    def _preset( self, value, lineNum ):
        if self.state != self.Start:
            print( "Phase error at line %d. Expected Start, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        try:
            self.id = int( value )
            self.state = self.SawId
            self.curr_address = None
            
        except ValueError:
            print( "Parse error at line %d. Expecting single integer." )
            sys.exit( 1 )

    def _ch( self, value, lineNum ):
        if self.state != self.SawId:
            print( "Phase error at line %d. Expected SawId, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        try:
            self.ch = int( value )
            self.state = self.SawCh
        except ValueError:
            print( "Parse error at line %d. Expecting single integer." % lineNum )
            sys.exit( 1 )

    def _addr( self, value, lineNum ):
        if self.state != self.SawCh and self.state != self.SawData:
            print( "Phase error at line %d. Expected SawCh or SawData, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        address_bytes = []
        for hex in value.split():
            address_bytes.append( int(hex,16) )

        self.curr_address = tuple( address_bytes )
        self.by_addr[ self.curr_address ] = []
        self.addr.append( address_bytes )
        self.state = self.SawAddr

    def _data( self, value, lineNum ):
        if self.state != self.SawAddr: 
            print( "Phase error at line %d. Expected SawAddr, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        data = []
        for hex in value.split():
            data.append( int(hex,16) )
        self.data.append( data )
        self.by_addr[ self.curr_address ].extend( data )
        self.state = self.SawData

    def _endPreset( self, value, lineNum ):
        if self.state != self.SawData:
            print( "Phase error at line %d. Expected SawData, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        try:
            endId = int( value )
        except ValueError:
            print( "Parse error at line %d. Expecting single integer." % lineNum )
            sys.exit( 1 )

        if endId != self.id:
            print( "Parse error at line %d. Preset number mismatch. Expected %d, but saw %d." % (lineNum, self.id, endId) )
            sys.exit( 1 )

        self.state = self.Done

    # Send current data set to amplifier
    def transmit( self, katanaObj ):
        # katanaObj.send_pc( self.ch )
        # sleep( 0.05 )

        for addr, data in zip( self.addr, self.data ):
            katanaObj.send_sysex_data( addr, data )

    # Print current data set to passed filehandle.
    def serialize( self, outfh ):
        outfh.write( "_preset %d\n" % self.id )
        outfh.write( "_ch %d\n" % self.ch )
        i = 0
        for addr, data in zip( self.addr, self.data ):
            if len(self.memo): outfh.write( "# %s\n" % self.memo[i] )
            
            hexstr = ' '.join( "%02x" % i for i in addr )
            outfh.write( "_addr %s\n" % hexstr )

            hexstr = ' '.join( "%02x" % i for i in data )
            outfh.write( "_data %s\n" % hexstr )
            i += 1
            
        outfh.write( "_endPreset %d\n" % self.id )

    # Controller input 0..127.  Scale this so it maxes out at the captured
    # volume. 
    def scale_volume_to_amp( self, controller_value ):
        if controller_value > 0:
            controller_value += 1
        return int( controller_value * self.volume_midi_scale )

    # Full range scaling when using built-in preset.
    # FIXME: No reason why we cannot read actual volume from
    # built-in.
    @staticmethod
    def scale_volume_to_amp_default( controller_value ):
        if controller_value > 0:
            controller_value += 1
        return int( controller_value * (100/128) ) 

    # Return array of bytes from current preset data. Call with
    # base address, offset and count.
    def get_data( self, address, offset, count ):
        if address in self.by_addr:
            bytes = self.by_addr[ address ]
            if offset + count > len( bytes ):
                count = len( bytes ) - offset
            return bytes[ offset : offset + count ]
        else:
            return []
        
if __name__ == '__main__':
    file = sys.stdout

    infh = open( "test.file", 'r' )

    objs = []
    for obj in PanelPreset.get_from_file( infh ):
        objs.append( obj )

    for obj in objs:
        obj.serialize( file )
        test_data = obj.get_data( (0x00,0x00,0x04,0x10), 18, 1 )
        print( "Test data = " + str(test_data).strip('[]') )
