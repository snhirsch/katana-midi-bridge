# Manage access to sysex addresses associated with 'complex' DSP
# devices (mod, fx)

import json
import sys
from pprint import pprint


class ComplexDSP:
    
    def __init__( self, parmfile ):
        with open(parmfile) as json_file:
            parms = json.load( json_file )

        # Build enum <--> name maps in both directions
        rec = parms['class']
        self.enum2name = {}
        self.name2enum = {}
        for val, name in zip( rec['values'], rec['display'] ):
            self.enum2name[val] = name
            self.name2enum[name] = val

        rec = parms['baseAddr']
        self.base_addr = {}
        for key, val in rec.items():
            self.base_addr[key] = val
            
        self.parameters = parms['parameters']
        self.master_key = parms['masterKey']
        
    # Call with category name of device (fx or mod) and class
    # (parametric, phaser, etc) enumeration value (from amp read)
    #
    # Returns class name and parameter block descriptor
    #
    def get_coords( self, category, class_enum ):
        # Lookup class name (T-Wah, Octave, ParametricEQ, etc)
        name = self.enum2name[class_enum]

        # Lookup parms blocks for global + active class
        base_table = self.base_addr[category]

        global_base = base_table['global']
        global_parms = self.parameters['global']

        dsp_base = base_table[name]
        dsp_parms = self.parameters[name]

        blocks = [ [global_base, global_parms['length']], [dsp_base, dsp_parms['length']] ]

        # Both mod and fx share the same global key setting
        if name == "PitchShifter":
            extra = [ self.master_key['baseAddr'], self.master_key['length'] ]
            blocks.append( extra )
        
        return { "name":name, "blocks":blocks }
        
            
if __name__ == '__main__':
    from katana import Katana
    import mido
    from color_buttons import ColorButtons

    mido.set_backend('mido.backends.rtmidi')

    args = sys.argv
    buttonObj = ColorButtons( args[1] )

    katana = Katana( "KATANA:KATANA MIDI 1 20:0", 1, False )
    dsp_recs = buttonObj.read_knobs( katana )

    # pprint( dsp_recs )

    complexObj = ComplexDSP( args[2] )
    
    for dsp_rec in dsp_recs:
        if dsp_rec['group'] == 'complex':
            coords = complexObj.get_coords( dsp_rec['category'], dsp_rec['type'] ) 
            print( "Name: ", coords['name'], ", Blocks: ", coords['blocks'] )
