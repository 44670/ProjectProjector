#/usr/bin/env python3   

import serial

ser = serial.Serial('/dev/ttyS0', 9600)

ser.write(b'\xff\x07\x99\x00\x00\x00\x00\xa0')