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

    # Static generator to create PanelPreset objects by parsing a
    # text file input stream
    #
    @staticmethod
    def get_from_file( infh ):
        lineNum = 0
        obj = PanelPreset()
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

    @staticmethod
    def read_from_amp( katana, preset_id ):
        obj = PanelPreset()
        obj.state = obj.Done
        obj.id = preset_id

        # NOTE: This code can hang or blow up with invalid list index if
        #       remnants from an earlier reply are sitting in the input
        #       buffer.

        # Enter edit mode
        katana.set_sysex_data( EDIT_ON )
        katana.set_sysex_data( EDIT_ON )
        preset_query = CURRENT_PRESET_ADDR[:]
        preset_query.extend( CURRENT_PRESET_LEN )
        dummy, preset = katana.get_sysex_data( preset_query )
        # Leave edit mode
        katana.set_sysex_data( EDIT_OFF )
        obj.ch = preset[0][1]

        # Normalize sysex-level preset id to the one presented on
        # public PC implementation.
        obj.ch -= 1
        if obj.ch < 0: obj.ch = 4

        # Read color assign and state
        addr, data = katana.get_sysex_data( COLOR_ASSIGN_QUERY )
        obj.addr.append( addr[0] )
        obj.data.append( data[0] )

        # Read amplifier panel block
        addr, data = katana.get_sysex_data( PANEL_STATE_QUERY )
        obj.addr.append( addr[0] )
        obj.data.append( data[0] )

        return obj

    def __init__( self ):
        self.state = self.Start
        self.id = -1
        self.ch = -1
        self.addr = []
        self.data = []

    def _preset( self, value, lineNum ):
        if self.state != self.Start:
            print( "Phase error at line %d. Expected Start, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        try:
            self.id = int( value )
            self.state = self.SawId
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

        address = []
        for hex in value.split():
            address.append( int(hex,16) )
        self.addr.append( address )
        self.state = self.SawAddr

    def _data( self, value, lineNum ):
        if self.state != self.SawAddr: 
            print( "Phase error at line %d. Expected SawAddr, but was %d." % (lineNum, self.state) )
            sys.exit( 1 )

        data = []
        for hex in value.split():
            data.append( int(hex,16) )
        self.data.append( data )
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

    def transmit( self, katanaObj ):
        katanaObj.send_pc( self.ch )
        sleep( 0.05 )

        for addr, data in zip( self.addr, self.data ):
            msg = []
            msg.extend( addr )
            msg.extend( data )
            katanaObj.set_sysex_data( msg )

    def serialize( self, outfh ):
        outfh.write( "_preset %d\n" % self.id )
        outfh.write( "_ch %d\n" % self.ch )
        for addr, data in zip( self.addr, self.data ):
            hexstr = ' '.join( "%02x" % i for i in addr )
            outfh.write( "_addr %s\n" % hexstr )

            hexstr = ' '.join( "%02x" % i for i in data )
            outfh.write( "_data %s\n" % hexstr )

        outfh.write( "_endPreset %d\n" % self.id )


if __name__ == '__main__':
    file = sys.stdout

    infh = open( "test.file", 'r' )

    objs = []
    for obj in PanelPreset.get_from_file( infh ):
        objs.append( obj )

    for obj in objs:
        obj.serialize( file )

