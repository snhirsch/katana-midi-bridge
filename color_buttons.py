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

        color_rec = parms['colorEnum']
        self.enum2name = {}
        self.name2enum = {}
        for val, name in zip( color_rec['values'], color_rec['display'] ):
            self.enum2name[val] = name
            self.name2enum[name] = val

        self.assign_index = parms['colorAssignIndex']

        assign2 = {}

        for knob in self.assign_index['knob'].keys():
            knob_rec = self.assign_index['knob'][knob]
            for range in knob_rec['range'].keys():
                range_rec = knob_rec['range'][range]
                assign2[range_rec['category']] = range_rec['colorOffset']

        self.assign_index2 = assign2

        self.active_index = parms['colorActiveIndex']

        self.knobs = parms['dspKnobs']

        self.color_state_xlate = parms['dspColorStateXlate']
        self.color_state = parms['dspColorState']

        self.knob_state_xlate = parms['dspKnobStateXlate']
        self.knob_state = parms['dspKnobState']

        self.simple = parms['dspSimple']
        self.complex = parms['dspComplex']
        
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

    def read_color_assign( self, katana ):
        assign_base_addr = self.assign_index['baseAddr']
        active_base_addr = self.active_index['baseAddr']
        result = []

        # First, scan assigned simple devices. Since all three colors share the
        # same set of parameters, we do only the currently active color.
        offsets = self.active_index['categoryOffset']
        for category in self.simple:
            color_enum = katana.query_sysex_byte( active_base_addr, offsets[category] )
            color = self.enum2name[color_enum]
            idx = self.assign_index2[category][color]
            type = katana.query_sysex_byte( assign_base_addr, idx )
            result.append( {"group":"simple", "category":category, "type":type} )

        # Complex devices have distinct parameter address ranges, so do all
        # colors
        for category in self.complex:
            for color in self.name2enum.keys():
                idx = self.assign_index2[category][color]
                type = katana.query_sysex_byte( assign_base_addr, idx )
                result.append( {"group":"complex", "category":category, "type":type} )

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

    result = buttonObj.read_color_assign( katana )
    pprint( result )
