# Manage access to sysex addresses associated with DSP 'color' buttons

import json
import sys
from pprint import pprint

# Terminology:
#
# Group:
#    Simple = boost, delay, reverb
#    Complex = mod, fx
#
# Category: boost, mod, delay, fx, reverb
#
# Model (simple group): Rat, OD+, spring, etc.
#
# Class (complex group): parametricEQ, rotary, etc.
#
# NOTE: category == class for simple group
#

class ColorButtons:
    
    def __init__( self, parmfile ):
        with open(parmfile) as json_file:
            parms = json.load( json_file )
        self.color_enum = parms['colorEnum']
        self.assign_index = parms['colorAssignIndex']
        self.active_index = parms['colorActiveIndex']
        self.knobs = parms['dspKnobs']
        self.color_state_xlate = parms['dspColorStateXlate']
        self.color_state = parms['dspColorState']
        self.knob_state_xlate = parms['dspKnobStateXlate']
        self.knob_state = parms['dspKnobState']

    # Scans amplifier state for DSP knobs and returns ordered array of
    # metadata records.
    #
    def read_knobs( self, katana ):
        offsets = self.knob_state['knobOffset']
        knob_base_addr = self.knob_state['baseAddr']
        assign_base_addr = self.assign_index['baseAddr']
        result = []
        
        for knob in self.knobs:
            # Read enumeration value for knob state
            state = katana.query_sysex_byte( knob_base_addr, offsets[knob] )

            # Lookup range (A/B) and color
            ( range, color ) = self.knob_state_xlate[state]
            # print( "Knob: %s, state: %d, range: %s, color: %s" % (knob, state, range, color) )

            # Knob is off?
            if range == "none": continue
            
            # Lookup group (simple/complex) and category (boost, delay, etc)
            rec = self.assign_index['knob'][knob]['range'][range]

            # Read enumeration value for active class (complex) or model (simple) 
            type = katana.query_sysex_byte( assign_base_addr, rec['colorOffset'][color] )
            result.append( {"group":rec['group'], "category":rec['category'], "type":type} )

        return result
            
if __name__ == '__main__':
    from katana import Katana
    import mido
    mido.set_backend('mido.backends.rtmidi')

    args = sys.argv
    buttonObj = ColorButtons( args[1] )

    katana = Katana( "KATANA:KATANA MIDI 1 20:0", 1, False )
    result = buttonObj.read_knobs( katana )
    pprint( result )

