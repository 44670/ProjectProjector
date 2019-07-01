#!/bin/bash

lircd-uinput -a &
mount /dev/mmcblk0p3 /disk
while true
do
	rm /run/next
	python shell.py
	source /run/next
	sleep 5
done


