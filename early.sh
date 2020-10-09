#!/bin/sh
if [ ! -e "/dev/ttyS0" ]; then
ln -s /dev/ttyAMA0 /dev/ttyS0
fi

python /root/early.py

cd /opt/shell
./autorun.sh &