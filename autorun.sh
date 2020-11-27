#!/bin/bash
killall lircd-uinput
lircd-uinput -a &
while true
do
	rm /run/next
	python shell.py
	source /run/next
	sleep 5
done


