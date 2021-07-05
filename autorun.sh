#!/bin/bash
cd /opt/shell
export LIBASOUND_THREAD_SAFE=0
killall bluealsa lircd-uinput
bluealsa -p a2dp-source &
lircd-uinput -a &
while true
do
	rm /run/next
	python3 main.py
	source /run/next
	sleep 5
done

