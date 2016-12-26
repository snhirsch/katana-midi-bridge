# katana-midi-bridge

# Introduction

The Katana (tm) amplifier responds to only a few MIDI program and
controller (PC and CC) messages. But dig a bit deeper and you'll
discover a rich sysex API on par with other Roland/Boss products like
the GT-100 guitar processor.  Roland has not made the Katana spec
public, but I was able to reverse-engineer and document a large
portion of it by observing USB communication between Boss Tone Studio
and the emplifier.

This program has three goals:

  1. Make use of the sysex API to provide an almost unlimited number
     of user-defined presets beyond the five built in to the
     amplifier.

  2. Make internal ("deep") parameters accessible through standard CC
     messages.

  3. Permit communication from 5-pin MIDI to the Katana combo amps
     (also requires a low-cost USB/MIDI converter).

The software is written in Python, a powerful cross-platform scripting
language. I use a Ubuntu Precise desktop machine for primary
development but routinely test on Raspberry Pi and Beagelbone embedded
computers to ensure these remain viable deployment targets.

(Due to occasional issues with USB on the RPi I am recommending the
BBG for live performance use)

Special thanks to:

  + Robert Fransson (aka Codesmart) of Primova Sound for feedback,
  encouragement and general programming wizardry.

  + All the regulars on VGuitar Forum for providing positive energy,
  enthusiasm and concrete suggestions.

## For the non-techies

I have written a Wiki page here:

https://github.com/snhirsch/katana-midi-bridge/wiki/Install

that attempts a detailed walk-through of the installation process on
Raspberry Pi or Beaglebone.  It's hard to know what level of detail to
hit and suggestions or comments would be appreciated if I've omitted
or glossed over something critical.

# Status

The extended preset feature is fully functional and allows you to save
and recall the entire front-panel state. All MIDI PC#s > 10 are fair
game and this should be enough for anyone.

I have implemented translation between CC# 70 and amplifier volume to
support foot-pedal MIDI controllers. Obviously more work is needed,
but the sysex definition is huge and I doubt any user will need access
to even a fraction of the internal parameter set. Rather than spend a
lot of time implementing adhoc mappings between CC and sysex, I'd like
to hear from the user community to see what people really need. 

One thought: Allow users to setup their own mappings by editing a text
file.

## Preset Behavior

My goal was to enable fast, glitch-free recall of bridge-managed user
presets. The built-in "Tone Settings" are able to instantly restore
snapshots of all deep parameters on every DSP based effect, but that's
done by block-copying chunks of data in memory at processor speed.
Trying to accomplish this by sending thousands of bytes of serial data
does not work all that smoothly.

After some thought, I made a philosophical decision that may seem a
bit strange: Use the "Tone Settings" as "platforms", or starting
points, for creating externally stored presets.  The idea is that you
configure pallettes of DSP effects (Boost, Delay, FX/Mod, Reverb) and
store them in the four built-in locations.  When you want to create a
user setting, start with a tone setting that has appropriate effects 
available.  Then, setup the front-panel controls (including the
effects "Color Buttons" and knobs) for your desired sound and tell the
bridge to store this state.  The bridge remembers which internal
preset you based your sound on and re-selects that before restoring
the front-panel settings.

So, we use the internal preset selection to rapidly configure deep
settings, then send a shorter burst of sysex commands to setup the
front panel.  This entire operation runs in about 50 msec. with
only negligible impact on sound.

# Overview of Installation

(See Wiki for step-by-step instructions)
  
## Prerequisites

  + For Ubuntu Precise or Debian Jessie the following packages must be
    present.  Install this first set with 'apt-get':

    - libasound2
    - librtmidi-dev
    - libusb-1.0-0-dev
    - libjack0 (Precise) 
    - libjackQ (Jessie)
    - at
    - python3
    - python3-dev
    - python3-pip
    - pyusb
    - mido

  + Then, use 'pip3' to install a couple of Python native modules:
```
$ pip3 install pyusb
$ pip3 install python-rtmidi
$ pip3 install mido
```
Would appreciate feedback on requirements for other distributions.

## Configuration

  1. Update ```60-controller.rules``` with the USB VID (vendor id) and PID
(product id) of your controller.  This edit affects (2) lines.

  2. Edit ```katana_bridge_start``` to set values marked as user
edits.  In addition to setting the USB vender and device id, you need
to specify which MIDI channel to listen on and provide a couple of
strings to help the program find the MIDI interface.

## Installation

Run the ```install.sh``` script as root

## Use

If you have configured everything correctly, the bridge will start
automatically when both the controller and the Katana amp are
connected via USB.  If either are disconnected (or shut off), the
bridge is stopped.

The vendor defined MIDI API is supported and will operate without any
change in behavior.  

To capture and store a user preset, dial in a sound to your liking and
"arm" the bridge for settings capture by sending three messages in
this format:

CC 3 - Value 127

within a two second period. Finally, select a program number in the
range 11..127 where you would like this stored. The bridge will save
the front-panel state and cycle the LEDs around the 'Amp Type' control
as an acknowledgement.  This information is permanently saved and can
be recalled instantly by re-selecting the PC#.

If you arm the bridge and change your mind, send any other CC message
to cancel.

I have the last preset on my Behringer FCB-1010 controller setup to
issue the CC3 command on a momentary basis.  When I want to capture a
setting, I tap this three times quickly than page through the banks
and press the preset where I wish to save.  This technique should be
possible with other floor controllers. 

## In case of difficulty

RPi and BBG are a bit fussy about enumeration of new USB devices. If
you are not getting proper communication, quit the program and try
replugging both the amp and MIDI controller **after** those devices
are powered up.

I've had success using a passive USB hub with the single USB on the
BBG, but YMMV since most USB<->5Pin MIDI converters draw some degree
of bus power.  A powered hub might be necessary in some situations.
