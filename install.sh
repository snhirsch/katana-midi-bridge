#!/bin/bash

BINDIR=/usr/local/bin
LIBDIR=/usr/local/share/katana
PARMDIR=$LIBDIR/parameters
INITDIR=/etc/init.d
UDEVDIR=/etc/udev/rules.d

if ! `grep -q katana-user /etc/passwd`; then
    echo "Create non-privileged user for MIDI bridge"
    useradd -m -s /bin/false -G plugdev,audio katana-user
fi

echo "Copy program and support scripts to $BINDIR"

cp -f katana_bridge_start $BINDIR
chmod 0755 $BINDIR/katana_bridge_start
chown root:root $BINDIR/katana_bridge_start

cp -f katana_bridge_stop $BINDIR
chmod 0755 $BINDIR/katana_bridge_stop
chown root:root $BINDIR/katana_bridge_stop

cp -f katana_bridge_app $BINDIR
chmod 0755 $BINDIR/katana_bridge_app
chown root:root $BINDIR/katana_bridge_app

echo "Copy Python modules and parameter files to $LIBDIR"
mkdir -p $LIBDIR
cp -f *.py $LIBDIR

mkdir -p $PARMDIR
cp -f ./parameters/*.json $PARMDIR

chown -R root:root $LIBDIR/*

echo "Copy init script to $INITDIR and register"

cp -f katana_bridge $INITDIR
chmod 0755 $INITDIR/katana_bridge
chown root:root $INITDIR/katana_bridge
update-rc.d katana_bridge defaults

# Run it right now to create the /var/run directory
$INITDIR/katana_bridge start

echo "Copy udev rules to $UDEVDIR and refresh system"

cp -f 50-katana.rules $UDEVDIR
chmod 0644 $UDEVDIR/50-katana.rules
chown root:root $UDEVDIR/50-katana.rules

cp -f 60-controller.rules $UDEVDIR
chmod 0644 $UDEVDIR/60-controller.rules
chown root:root $UDEVDIR/60-controller.rules

udevadm control --reload

echo "Done!"
