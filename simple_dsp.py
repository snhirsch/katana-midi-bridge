# Manage access to sysex addresses associated with 'simple' DSP
# devices (boost, delay, reverb)

import json
import sys
from pprint import pprint


class SimpleDSP:
    
    def __init__( self, parmfile ):
        with open(parmfile) as json_file:
            parms = json.load( json_file )

        # Build enum <--> name maps in both directions
        self.models = {}
        for key, rec in parms['models'].items():
            enum2name = {}
            name2enum = {}
            for val, name in zip( rec['values'], rec['display'] ):
                enum2name[val] = name
                name2enum[name] = val

            self.models[key] = {}
            self.models[key]['enum2name'] = enum2name
            self.models[key]['name2enum'] = name2enum
            
        self.parameters = parms['parameters']

    # Call with category of device (boost, delay, reverb) and model
    # (Rat, OD+, etc) enumeration value (from amp read)
    #
    # Returns model name and parameter block descriptor
    #
    def get_coords( self, category, model_enum ):
        # Lookup model name (TrebleBoost, BluesDrive, Spring, Hall, etc)
        name = self.models[category]['enum2name'][model_enum]

        # Lookup address and length of DSP device parms
        parms = self.parameters[category]
        base_addr = parms['baseAddr']
        length = parms['length']

        return { "name":name, "blocks":[ [base_addr, length] ] }
        
            
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

    simpleObj = SimpleDSP( args[2] )
    
    for dsp_rec in dsp_recs:
        if dsp_rec['group'] == 'simple':
            coords = simpleObj.get_coords( dsp_rec['category'], dsp_rec['type'] ) 
            print( "Name: ", coords['name'], ", Blocks: ", coords['blocks']  )
