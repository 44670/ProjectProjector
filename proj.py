import os
import time
import const



def powerOff():
    sendCmd(0x02)
    time.sleep(1)
    sendCmd(0x0B, [0x00])
    time.sleep(5)
    setPowerMosfet(0)

def powerOn():
    setPowerMosfet(1)
    time.sleep(7)
    # Start Input
    sendCmd(0x01)

def stopInput():
    sendCmd(0x02)
    time.sleep(1)

def startInput():
    sendCmd(0x01)
    time.sleep(1)

def resetUserParam():
    sendCmd(0x08)
    time.sleep(10)

def saveUserParam():
    sendCmd(0x07, [0, 0, 1, 1, 1])
    time.sleep(10)

def coaxBegin():
    sendCmd(0x32)

def coaxDown():
    sendCmd(0x33)

def coaxUp():
    sendCmd(0x34)

def coaxNext():
    sendCmd(0x32)

def coaxEnd():
    sendCmd(0x35, [0])

def osciBegin():
    sendCmd(0x36)

def osciDown():
    sendCmd(0x37)

def osciUp():
    sendCmd(0x38)

def osciNext():
    sendCmd(0x36)

def osciEnd():
    sendCmd(0x39, [0])




if os.name == 'nt':
    #import usb.core
    #dev = usb.core.find(idVendor=0x4348, idProduct=0x5593)
    def sendCmd(cmd, data=[]):
        print("sendCmd", cmd, data)
        #dev.write(0x02, [0x77, cmd, len(data)] + data)
    def setPowerMosfet(on):
        print("setPowerMosfet", on)
    def setSpeaker(on):
        print("setSpeaker", on)
else:
    if const.HW_MODEL == 'v2':
        import smbus
        sm = smbus.SMBus(1)
        def sendCmd(cmd, data=[]):
            sm.write_i2c_block_data(0x77,cmd,[len(data)] + data)
        
        import gpiozero
        i2s_cr = gpiozero.LED(23)
        i2s_cl = gpiozero.LED(22)
        mos = gpiozero.LED(27)
        
        def setSpeaker(on):
            if on:
                i2s_cr.on()
                i2s_cl.on()
            else:
                i2s_cr.off()
                i2s_cl.off()

        def setPowerMosfet(on):
            if on:
                mos.on()
            else:
                mos.off()
    else:
        import serial
        ser = serial.Serial('/dev/ttyS0', 9600)
        def sendCmd(cmd, data=[]):
            print("sendCmd not supported on v1", cmd, data)
        def setPowerMosfet(on):
            print("setPowerMosfet", on)
        def setSpeaker(on):
            print("setSpeaker", on)
