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

New:

  + Preset capture / restore now preserves all DSP effect deep
    settings in addition to front panel knobs and color buttons. My
    initial scheme (so-called "palettes") was not terribly
    practical and the new behavior is more what a user would expect.

  + Preset capture / restore no longer pays attention to built-in
    presets (aka "Tone Settings"). It simply takes a complete snapshot
    of the active amplifier state at save and replaces the current
    state with that saved snapshot at restore.  Restore does **not**
    overwrite the current "Tone Setting", although you can choose to
    do that manually if you wish.

The extended preset feature allows you to save and recall the **entire**
amplifier state:

  + All 15 assigned DSP effects
  + Effects chain
  + Noise-gate setting
  + All front panel controls other than Master, Power Control and Tone
  Setting. (Includes selected ranges and colors in the Effects section)

For example, if you have a chorus voice active on green color in the
FX slot and a pitch-shifter tuned in on yellow the bridge will capture
both of them (along with whatever was on red!) so you can toggle the
effect type on your recalled setting and get exactly what you expect.
Similarly, the bridge stores whatever is setup on the inactive range
of the Boost/Mod and Delay/Fx knobs. So, to continue the previous
example, if you had a particular delay type mapped to red you will get
that back after recall when you move the Delay/Fx knob to the first
half of its range.

At this point I am not capturing the effects loop settings, although
this is under consideration for a future release.  If it's important
to you, please weigh in by opening an issue.

You may instruct the bridge software to store the amplifier state in
MIDI PC# 11-127 as you choose (discussed below).  The data is stored
in a small disk file on the computer, not the amplifier itself. This
file is plain text and you can edit it yourself if you know what
you're doing. 

Mapping of CC values is very limited at this point.  Robert Fransson
(Codesmart) and I have worked out a full specification that maps CC#
to almost all functions in the amplifier.  He has completely
implemented this in the Primova Sound MIDX-20 product.  I fully
intend to do the same in my code as time permits.  

At this point, the only CC# mapping is:

CC# 70 (0-127) --> Amplifier Volume (0-100)

Volume preset handling needs some explanation. I find it annoying when
preset recall maps expression pedal toe-down to full volume,
regardless of where you might have had the volume when shaping your
tone.  The logic in this program ensures that toe-down on recall gives
you exactly the volume position that existed at save. I realize this
may not be everyone's preference and will keep an open mind to
suggestions or criticism.

NOTE: This range limiting does **not** apply to the built in "Tone
Settings", but only to presets managed by the bridge program.

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
as an acknowledgment.  This information is permanently saved and can
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
you are not getting proper communication, try replugging both the amp
and MIDI controller **after** those devices are powered up.

I've had success using a passive USB hub with the single USB on the
BBG, but YMMV since most USB<->5Pin MIDI converters draw some degree
of bus power.  A powered hub might be necessary in some situations.
