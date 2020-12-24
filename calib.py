import pygame

from pygame.locals import *
import time
import sys
import os
import serial
import binascii

serial = serial.Serial('/dev/ttyS0', 9600)
LED_BASEDIR = '/sys/class/leds/led0/'

def pollKey():
    while True:
        event = pygame.event.poll()
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYUP:
            return event.key

def waitKey(timeout=None):
    timePassed = 0
    while True:
        evt = pollKey()
        if (evt != None):
            return evt
        time.sleep(0.1)
        timePassed += 100
        if (timeout != None) and (timePassed >= timeout):
            return None

def tryWriteFile(fn, data):
    try:
        with open(fn, 'wb') as f:
            f.write(data)
    except Exception as e:
        print(e)

def ledOnAndWait(offAfterSeconds):
    global ledCounter
    tryWriteFile(LED_BASEDIR + 'brightness', '0')
    time.sleep(offAfterSeconds)
    tryWriteFile(LED_BASEDIR + 'brightness', '1')

def submitSerialCommand(cmd):
    if (len(cmd) != 7):
        return -1
    cksum = 0
    for ch in cmd[1:]:
        cksum += ord(ch)
    cksum &= 0xFF
    cmd += chr(cksum)
    serial.write(cmd)
    print(binascii.hexlify(cmd))
    ledOnAndWait(0.2)

def sendCmd(c):
    s = ''
    for b in c:
        if b == -1:
            b = 255
        s += chr(b)
    submitSerialCommand(s)

def calibCoax():
    sendCmd(DEBUG_SIGNAL_OFF)
    ledOnAndWait(10)
    sendCmd(DEBUG_COAXIALITY)
    while True:
        key = waitKey()
        if key == K_UP:
            sendCmd(DEBUG_COAXIALITY_SUBTRACTION)
        if key == K_DOWN:
            sendCmd(DEBUG_COAXIALITY_ADD)
        if key == K_SPACE:
            sendCmd(DEBUG_COAXIALITY)
        if key == K_ESCAPE:
            sendCmd(DEBUG_COAXIALITY_OUT)
            break
    ledOnAndWait(5)
    sendCmd(DEBUG_SIGNAL_ON)
    ledOnAndWait(10)

def calibOsci():
    sendCmd(DEBUG_SIGNAL_OFF)
    ledOnAndWait(10)
    sendCmd(DEBUG_OSCILLATOR)
    while True:
        key = waitKey()
        if key == K_UP:
            sendCmd(DEBUG_OSCILLATOR_SUBTRACTION)
        if key == K_DOWN:
            sendCmd(DEBUG_OSCILLATOR_ADD)
        if key == K_SPACE:
            sendCmd(DEBUG_OSCILLATOR)
        if key == K_ESCAPE:
            sendCmd(DEBUG_OSCILLATOR_OUT)
            break
    ledOnAndWait(5)
    sendCmd(DEBUG_SIGNAL_ON)
    ledOnAndWait(10)

DEBUG_SIGNAL_ON = [ -1,  7,  1,  0,  0,  0,  0]
DEBUG_SIGNAL_OFF = [ -1,  7,  3,  0,  0,  0,  0]
DEBUG_COAXIALITY = [ -1,  7,  21,  0,  0,  0,  0]
DEBUG_COAXIALITY_ADD = [ -1,  7,  23,  0,  0,  0,  0]
DEBUG_COAXIALITY_SUBTRACTION = [ -1,  7,  25,  0,  0,  0,  0]
DEBUG_COAXIALITY_OUT = [ -1,  7,  27,  0,  0,  0,  0]
DEBUG_COAXIALITY_SAVEOUT = [ -1,  7,  37,  0,  0,  0,  0]
DEBUG_OSCILLATOR = [ -1,  7,  29,  0,  0,  0,  0]
DEBUG_OSCILLATOR_ADD = [ -1,  7,  31,  0,  0,  0,  0]
DEBUG_OSCILLATOR_SUBTRACTION = [ -1,  7,  33,  0,  0,  0,  0]
DEBUG_OSCILLATOR_OUT = [ -1,  7,  35,  0,  0,  0,  0]
DEBUG_OSCILLATOR_SAVEOUT = [ -1,  7,  39,  0,  0,  0,  0]

SCREEN_H = 720
SCREEN_W = 1280

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

COLOR_BG = BLACK
COLOR_FG = WHITE
COLOR_MENU_SEL = (24, 242, 192)
COLOR_LINE = (127, 127, 127)


pygame.display.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), 0, 32)


screen.fill(BLACK)
screen.fill(WHITE, (0, 100, SCREEN_W, 2))
screen.fill(WHITE, (0, 75, SCREEN_W, 1))
screen.fill(WHITE, (0, 50, SCREEN_W, 2))
screen.fill(WHITE, (0, 25, SCREEN_W, 1))
screen.fill(WHITE, (10, 110, 1, 500))
screen.fill(WHITE, (1000, 110, 1, 500))
screen.fill(RED, (200, 200, 50, 50))
screen.fill(GREEN, (300, 200, 50, 50))
screen.fill(BLUE, (400, 200, 50, 50))
pygame.display.update()

while True:
    key = waitKey()
    if key == K_1:
        calibCoax()
    if key == K_3:
        calibOsci()
    if key == K_RETURN:
        break
