#!/usr/bin/python3
#
# Represent a preset 
#
#

import sys
import re
from time import sleep
from globals import *
from pprint import pprint

class ParmRec:
    def __init__( self, addr=None, data=None, memo="" ):
        self.addr = addr
        self.data = data
        self.memo = memo

    def to_string( self ):
        print( "Memo: ", self.memo )
        print( "Addr: ", self.addr )
        print( "Data: ", self.data )

class PanelPreset:

    # Track object state
    Start, SawId, SawAddr, SawData, Done = range( 5 )

    # Static generator to create multiple PanelPreset objects by parsing a
    # text file input stream
    #
    @staticmethod
    def get_from_file( infh ):
        rx = re.compile( '#\s*' )

        lineNum = 0
        obj = PanelPreset()
        for line in infh:
            lineNum += 1
            line = line.strip()
            if len( line ) == 0: continue
            if re.match( r'^#', line ):
                # If we're in a preset stanza gather comments, removing any
                # '#' char prefix.
                if obj.curr_rec != None:
                    obj.curr_rec.memo += rx.sub( '', line )
                continue

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
                yield obj
                obj = PanelPreset()
                
        if obj.state != obj.Start:
            print( "Parse error at line %d." % lineNum )

    # Static factory method to create a single PanelPreset object by reading
    # current amplifier state
    #
    @staticmethod
    def read_from_amp( katana, preset_id, rangeObj ):
        obj = PanelPreset()
        obj.state = obj.Done
        obj.id = preset_id

        for rec in rangeObj.get_coords():
            first = rec['baseAddr']
            last = rec['lastAddr']
            name = rec['name']
            addr, data = katana.query_sysex_range( first, last )
            for a, d in zip( addr, data ):
                parm = ParmRec( a, d, name )
                obj.parms.append( parm )
        
        return obj

    def __init__( self ):
        self.state = self.Start
        self.id = -1

        self.by_addr = {}
        self.curr_rec = None
        self.parms = []
        
    # State machine handlers for parsing data file:
        
    def _preset( self, value, lineNum ):
        if self.state != self.Start:
            print( "Phase error at line %d. Expected Start, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        try:
            self.id = int( value )
            self.curr_rec = ParmRec()
            self.state = self.SawId

        except ValueError:
            print( "Parse error at line %d. Expecting single integer." )
            sys.exit( 1 )

    def _addr( self, value, lineNum ):
        if self.state != self.SawId and self.state != self.SawData:
            print( "Phase error at line %d. Expected SawId or SawData, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        address_bytes = []
        for hex in value.split():
            address_bytes.append( int(hex,16) )

        self.curr_rec.addr = tuple( address_bytes )
        self.state = self.SawAddr

    def _data( self, value, lineNum ):
        if self.state != self.SawAddr: 
            print( "Phase error at line %d. Expected SawAddr, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        data = []
        for hex in value.split():
            data.append( int(hex,16) )

        self.curr_rec.data = tuple( data )
        self.parms.append( self.curr_rec )
        self.by_addr[ self.curr_rec.addr ] = self.curr_rec
        self.curr_rec = ParmRec()
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
        for parm in self.parms:
            if parm.addr[0] == 0xff:
                sleep( parm.data[0]/1000 )
                continue

            katanaObj.send_sysex_data( parm.addr, parm.data )

    # Print current data set to passed filehandle.
    def serialize( self, outfh ):
        outfh.write( "_preset %d\n" % self.id )
        i = 0
        for parm in self.parms:
            if len(parm.memo): outfh.write( "# %s\n" % parm.memo )
            
            hexstr = ' '.join( "%02x" % i for i in parm.addr )
            outfh.write( "_addr %s\n" % hexstr )

            hexstr = ' '.join( "%02x" % i for i in parm.data )
            outfh.write( "_data %s\n" % hexstr )
            i += 1
            
        outfh.write( "_endPreset %d\n" % self.id )

    # Return array of bytes from current preset data. Call with
    # base address, offset and count.
    def get_data( self, address, offset, count ):
        if address in self.by_addr:
            parm = self.by_addr[ address ]
            bytes = parm.data
            if offset + count > len( bytes ):
                count = len( bytes ) - offset
            return bytes[ offset : offset + count ]
        else:
            return []
        
if __name__ == '__main__':
    
    args = sys.argv

    file = sys.stdout

    infh = open( args[1], 'r' )

    objs = []
    for obj in PanelPreset.get_from_file( infh ):
        objs.append( obj )

    for obj in objs:
        for parm in obj.parms:
            print( "-----" )
            parm.to_string()
            print( "---" )
            
        obj.serialize( file )
        test_data = obj.get_data( PANEL_STATE_ADDR, 0, 1 )
        print( "Test data = " + str(test_data).strip('[]') )
