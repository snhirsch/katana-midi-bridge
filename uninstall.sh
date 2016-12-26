#!/bin/bash

BINDIR=/usr/local/bin
LIBDIR=/usr/local/share/katana
INITDIR=/etc/init.d
UDEVDIR=/etc/udev/rules.d

if `grep -q katana-user /etc/passwd`; then
    echo "Remove non-privileged user for MIDI bridge"
    userdel -r katana-user
fi

echo "Remove program and support scripts from $BINDIR"

rm -f $BINDIR/katana_bridge_start
rm -f $BINDIR/katana_bridge_stop
rm -f $BINDIR/katana_bridge_app

echo "Remove Python modules from $LIBDIR"
rm -rf $LIBDIR

echo "Remove init script from $INITDIR"

rm -f $INITDIR/katana_bridge
update-rc.d katana_bridge remove

echo "Remove udev rules from $UDEVDIR and refresh system"

rm -f $UDEVDIR/50-katana.rules
rm -f $UDEVDIR/60-controller.rules

udevadm control --reload

echo "Done!"
