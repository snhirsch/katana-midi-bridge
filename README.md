# katana-midi-bridge

# Introduction

The Katana (tm) amplifier responds to only a few MIDI program and
controller (PC and CC) messages. But dig a bit deeper and you'll
discover a rich sysex API on par with other Roland/Boss products like
the GT-100 guitar processor.  Roland has not made the Katana spec
public, but I was able to reverse-engineer and document a large
portion of it by observing USB communication between Boss Tone Studio
and the amplifier.

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

  + Robert Fransson (Codesmart) of Primova Sound for feedback,
  encouragement and general programming wizardry.

  + All the regulars on VGuitar Forum for providing positive energy,
  enthusiasm and concrete suggestions. In particular I salute Colin
  Willcocks (Gumtown) and Robin Van Boven (Beanow) for their
  invaluable contributions to Katana reverse-engineering.  And, as
  always, Steve Conrad (Elantric) for providing the most valuable
  forum on Earth for musical propellor-heads.

## For the non-techies

I have written a Wiki page here:

https://github.com/snhirsch/katana-midi-bridge/wiki/Install

that attempts a detailed walk-through of the installation process on
Raspberry Pi or Beaglebone.  It's hard to know what level of detail to
hit and suggestions or comments would be appreciated if I've omitted
or glossed over something critical.

# Status

New:

  + Preset capture/restore now preserves all relevant settings in the
    "patch data" area. This is a superset of what's available on the
    front panel, so knobs and color buttons are no longer directly
    captured.

    Rationale:

    Katana has numerous capabilities beyond what's exposed in the Boss
    Tone Studio or reachable from panel knobs. It's incredibly
    difficult to get sensible interaction between physical controls
    and a recalled patch, so for now I'm not even going to try.

  + The bridge now interrupts audio output in a distinctive pattern to
  acknowledge patch capture.  The previous approach of cycling the amp
  model LEDs was slow and resulted in undesirable side-effects.  This
  is discussed in more detail below.

The bridge software stores patches outside the amplifier and can
recall them upon receipt of a MIDI PC command.

Mapping of CC values is very limited at this point.  Robert Fransson
(Codesmart) and I have worked out a full specification that maps CC#
to almost all functions in the amplifier.  He has completely
implemented this in the Primova Sound MIDX-20 product.  I fully
intend to do the same in my code as time permits.  

At this point, the only CC# mapping is:

CC# 70 (0-127) --> Amplifier Volume (0-100)

Previous versions of this application tied the MIDI volume controller
to the amplifier volume and used a complex approach to ensure pedal
toe-down never exceeded the setting at capture time.  CC# 70 in this
release is tied to the internal volume pedal controller where it
inherently behaves in the desired manner (this is what a volume pedal
connected to the GA-FC footswitch acts upon).

The vendor defined MIDI API is supported and will operate without any
change in behavior.  

### IMPORTANT: Backwards Compatibility

If you wish to keep patches produced by earlier versions of this
program they must be converted to the new format using the
'katana_convert' program.  It may be run on a desktop PC or the
embedded computer you're using for performance (Beaglebone or RPi).

Install the new software first, then:

  1. If running on your performance rig, disconnect the MIDI
  controller to ensure the bridge is not running.

  2. Connect the amplifier

  3. Determine the amplifier MIDI interface using the same method as
  during initial installation.  See Wiki for details.

  4. Run the conversion (your parms may vary):

  katana_convert "KATANA:KATANA MIDI 1 20:0" 1 <old_file> <new_file>

  Where 'old_file' is the path of the existing patch file (usually
  /home/katana-user/preset.data) and 'new_file' is where you want to
  save the converted output.  Do not use the same name for both!

  5. After the conversion runs, save a copy of the old file for
  safety, rename the new file to 'preset.data' and copy it into the
  /home/katana-user directory.

# High-Level Overview of Installation

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

  2. Update ```50-katan.rules``` with the USB VID (vendor id) and PID
(product id) of your amp.  This requirement will go away once I learn the 
USB product ids for all Katana models

  3. Edit ```katana_bridge_start``` to set values marked as user
edits.  In addition to setting the USB vender and device id, you need
to specify which MIDI channel to listen on and provide a couple of
strings to help the program find the MIDI interface.

## Installation

Run the ```install.sh``` script as root

## Communication Test

First, ensure that your controller is on and connected to the Katana
bridge computer. Then, connect the amp to that computer. If you have
configured everything correctly, the bridge will start automatically.

Wait about ten seconds for the software to initialize.

Check basic operation by sending PC# 1-5 while watching the "Tone
Settings" LEDs, which should change accordingly.  If you have a volume
control or pedal mapped to CC# 70, check to see if it is able to vary
the amplifier volume.  If the amp does not react, see section on
troubleshooting below.

When either the amp or controller is disconnected (or shut off), the
bridge will automatically be stopped.

## Use

To capture and store a user preset, start by dialing in a sound to
your liking.  This might involve connecting the amp to Boss Tone
Studio or Gumtown's Katana FxFloorboard application (required if you
want access to hidden settings). After you setup a tone to your
liking the next step depends on which application was used:

If you were connected to FxFloorboard (recommended), check the
rectangular "Connect" button at the top of the window.  If it is
illuminated in green, toggle the connection state off by clicking on
the button.

If you used BTS, exit that program by closing the window.

**IMPORTANT**: Physically disconnecting without taking one of these
steps leaves the amplifier in "edit" mode. If reconnected to USB while
in that mode it discards your carefully crafted patch and restores the
current preset or panel state. In other words, you lose all your work.

Disconnect the amp from the computer and plug it into the device where
you've installed Katana bridge. Wait about ten seconds for the program
to start.

Arm the bridge for settings capture by sending three messages in this
format:

CC#: 3 - Value: 127

within a two second period.  Then strike and hold a chord and select a
program number in the range 11..127 where you would like to store your
settings. The bridge will read and save the patch data and pulse the
volume to acknowledge. This information is permanently saved and can
be recalled instantly by re-selecting the PC#.

If you change your mind after arming the bridge send any other CC
message to cancel.

I have the last preset on my Behringer FCB-1010 controller setup to
issue the CC3 command on a momentary basis.  When I want to capture a
setting, I tap this three times quickly then page through the banks
and press the preset where I wish to save.  This technique should be
possible with other floor controllers. 

## In case of difficulty

Check the system logs (/var/log/syslog and /var/log/messages) to see
if the amp and controller were detected.  The bridge code will not
start until they're both seen.

Check the mail spool file for 'root' to see if any exceptions or error
messages are present.

RPi and BBG are a bit fussy about enumeration of new USB devices. If
you are not getting proper communication, try replugging both the amp
and MIDI controller **after** those devices are powered up.

I've had success using a passive USB hub with the single USB on the
BBG, but YMMV since most USB<->5Pin MIDI converters draw some degree
of bus power.  A powered hub might be necessary in some situations.

If all else fails, open an issue here and I'll try to help.  Please
describe as much as you can about your environment and what you have
tried.
