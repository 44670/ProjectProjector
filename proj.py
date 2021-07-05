import os
import time

if os.name == 'nt':
    def sendCmd(cmd, data):
        print("sendCmd", cmd, data)
    def setPowerMosfet(on):
        print("setPowerMosfet", on)
else:
    import smbus
    sm = smbus.SMBus(1)
    def sendCmd(cmd, data):
        sm.write_i2c_block_data(0x77,cmd,data)
    

def powerOff():
    sendCmd(0x02, [0x00])
    time.sleep(1)
    sendCmd(0x0B, [0x01, 0x00])
    time.sleep(5)
    setPowerMosfet(0)

def powerOn():
    setPowerMosfet(1)
    time.sleep(7)
    # Start Input
    sendCmd(0x01, [0x00])