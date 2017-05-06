# Manage bulk save/restore 

import json
import sys
from pprint import pprint

class Range:
    
    def __init__( self, parmfile ):
        with open(parmfile) as json_file:
            self.recs = json.load( json_file )

    def get_coords( self ):
        return self.recs
            
if __name__ == '__main__':
    from katana import Katana
    from pretty_print import PrettyPrinter
    import mido
    import timeit

    args = sys.argv
    
    mido.set_backend('mido.backends.rtmidi')

    katana = Katana( "KATANA:KATANA MIDI 1 20:0", 1, False )
    rangeObj = Range( args[1] )

    printer = PrettyPrinter( sys.stdout )
    for rec in rangeObj.get_coords():
        print( "Range = ", rec['name'] )
        pprint( rec )
        first = rec['baseAddr']
        last = rec['lastAddr']
        start_time = timeit.default_timer()
        addr, data = katana.query_sysex_range( first, last )
        chunks = len( addr )
        elapsed = timeit.default_timer() - start_time
        printer.format( addr, data )
        print( "\nRead %d chunks in %f sec." % (chunks, elapsed) )

        
