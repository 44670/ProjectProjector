# -*- coding: utf-8 -*-
from pygame.locals import *
from gpiozero import Button
import struct
import binascii
import pygame.freetype
import pygame
import subprocess
import time
import sys
import os
import serial

import mediarenderer


VIDEO_PATH = '/disk/video'
FONT_PATH = '/opt/shell/font.ttf'


button = Button(17)
serial = serial.Serial('/dev/ttyS0', 9600)

CMD_TOGGLE_POWER = '\xff\x07\x99\x00\x00\x00\x00'

PROJECTOR_ARGS = [
    ('Brightness', -31, 10, 41),
    ('Contrast', -15, 15, 43),
    ('Sharpness', 0, 6, 49),
    ('DistortionUpDown', -20, 30, 53),
    ('DistortionLeftRight', -30, 30, 51),
    ('HueU', -15, 15, 45),
    ('HueV', -15, 15, 45),
    ('SaturationU', -15, 15, 47),
    ('SaturationV', -15, 15, 47),
]

projectorArgValue = [0] * 9


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
    time.sleep(0.2)
    if cmd[2] in ['\x99', '\x0b', '\x01', '\x77']:
        renderMessageBox('Please Wait...', '')
        time.sleep(40)
        flushKey()


os.environ['SDL1_VIDEODRIVER'] = 'dispmanx'
os.environ['SDL_NOMOUSE'] = '1'

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


# pygame.init()
pygame.display.init()
pygame.freetype.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), 0, 32)
basicFont = pygame.freetype.Font(FONT_PATH, 48)
basicFontHeight = basicFont.get_sized_height()
itemHeight = basicFontHeight + 10

screen.fill(BLACK)
pygame.display.update()


def runCommandAndGetOutput(args):
    print('runCommand', args)
    ret = subprocess.check_output(args)
    print(ret)
    return ret

def pollGpioKey():
    if not button.is_pressed:
        return None
    pressCount = 0
    while True:
        pressCount += 1
        while button.is_pressed:
            time.sleep(0.01)
        for i in range(0, 50):
            time.sleep(0.01)
            if button.is_pressed:
                break
        if i >= 49:
            break
    if pressCount == 1:
        return K_DOWN
    if pressCount == 2:
        return K_UP
    if pressCount == 3:
        return K_RIGHT
    if pressCount == 4:
        return K_LEFT
    if pressCount == 5:
        return K_ESCAPE
    return None


def pollKey():
    while True:
        event = pygame.event.poll()
        if event.type == NOEVENT:
            return pollGpioKey()
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


def flushKey():
    while waitKey(200) != None:
        pass


def callOMXPlayer(url, srt=None, mode=None):
    screen.fill(COLOR_BG)
    updateScreen()

    aplayRet = runCommandAndGetOutput(['aplay', '-l'])
    args = ['/usr/bin/omxplayer.bin']
    args += ['--win', '0,0,%d,%d' % (SCREEN_W, SCREEN_H)]
    if (aplayRet.find('card 1:') != -1):
        print('Using usb sound card...')
        args += ['-o', 'alsa:hw:1,0']
    args += ['--font', FONT_PATH, '--italic-font', FONT_PATH]
    args += ['--timeout', '120']
    args += ['--vol', '-2100']
    if srt:
        args += ['--subtitles', srt]
    if mode == 'tv':
        args += ['--live']
        args += ['--threshold', '5']
        args += ['--avdict', 'reconnect:1,reconnect_at_eof:1,reconnect_streamed:1,reconnect_delay_max:60']
    elif mode == 'dlna':
        args += ['--threshold', '5']
        args += ['--avdict', 'reconnect:1,reconnect_at_eof:1,reconnect_streamed:1,reconnect_delay_max:60']
    args += [url]
    proc = subprocess.Popen(args=args, stdout=None, stdin=subprocess.PIPE)
    while proc.poll() is None:
        key = waitKey(500)
        if mode == 'tv':
            if (key == K_LEFT) or (key == K_RIGHT):
                proc.terminate()
                return key
        else:
            if key == K_RIGHT:
                proc.stdin.write("\x1B[C")
                proc.stdin.flush()
            elif key == K_LEFT:
                proc.stdin.write("\x1B[D")
                proc.stdin.flush()
            elif key == K_1:
                proc.stdin.write("\x1B[B")
                proc.stdin.flush()
            elif key == K_3:
                proc.stdin.write("\x1B[A")
                proc.stdin.flush()
        if key == K_UP:
            proc.stdin.write('+')
            proc.stdin.flush()
        elif key == K_DOWN:
            proc.stdin.write('-')
            proc.stdin.flush()
        elif key == K_ESCAPE:
            proc.terminate()
            return None
        elif key == K_SPACE:
            proc.stdin.write(' ')
            proc.stdin.flush()
        

    return None


def handlePowerButton():
    print('---power button pressed---')
    submitSerialCommand(CMD_TOGGLE_POWER)


def updateScreen():
    pygame.display.update()


def drawText(x, y, text, colorFg, colorBg):
    return basicFont.render_to(screen, (x, y), text, colorFg, colorBg)


def clearAndDrawTitle(title):
    screen.fill(COLOR_BG)
    screen.fill(COLOR_FG, (0, itemHeight - 3, SCREEN_W, 2))
    drawText(10, 5, title, COLOR_FG, COLOR_BG)


def renderMessageBox(title, msg):
    clearAndDrawTitle(title)
    drawText(30, itemHeight + 10, msg, COLOR_FG, COLOR_BG)
    updateScreen()


def drawBorder(x, y, w, h, borderWidth, borderColor):
    screen.fill(borderColor, (x, y, w, borderWidth))
    screen.fill(borderColor, (x, y + h - borderWidth, w, borderWidth))
    screen.fill(borderColor, (x, y, borderWidth, h))
    screen.fill(borderColor, (x + w - borderWidth, y, borderWidth, h))

SWKBD_MAP = [None] * 3
SWKBD_MAP[0] = '1234567890abcdefghijklmnopqrstuvwxyz'
SWKBD_MAP[1] = SWKBD_MAP[0].upper()
SWKBD_MAP[2] = r"""~`@#$%^&*+-_=<>()[]{}\|/;:'",.?!    """
SWKBD_FUNC = ['<-', '[ ]', 'Aa.', 'OK']

def inputDialog(title, text):
    KBD_GRID_SIZE = 80
    kbdMode = 0
    kbdSelection = 0
    if text == None:
        text = ''
    while True:
        clearAndDrawTitle(title)
        drawText(30, itemHeight + 10, text + '_', COLOR_FG, COLOR_BG)
        drawBorder(0, itemHeight, SCREEN_W, itemHeight, 2, COLOR_FG)
        for i in range(0, 40):
            if i < 36:
                t = SWKBD_MAP[kbdMode][i]
            else:
                t = SWKBD_FUNC[i - 36]
            x = KBD_GRID_SIZE * (i % 10)
            y = SCREEN_H - (KBD_GRID_SIZE * (4 - i / 10))
            drawText(x + 10, y + 10, t, COLOR_FG, COLOR_BG)
            if kbdSelection == i:
                drawBorder(x, y, KBD_GRID_SIZE, KBD_GRID_SIZE, 3, COLOR_MENU_SEL)
        updateScreen()
        key = waitKey()
        if key == K_DOWN:
            kbdSelection += 10
        elif key == K_UP:
            kbdSelection -= 10
        elif key == K_LEFT:
            kbdSelection -= 1
        elif key == K_RIGHT:
            kbdSelection += 1
        elif key == K_ESCAPE:
            return None
        elif (key == K_RETURN) or (key == K_SPACE):
            if kbdSelection == 36:
                text = text[:-1]
            elif kbdSelection == 37:
                text += ' '
            elif kbdSelection == 38:
                kbdMode += 1
            elif kbdSelection == 39:
                return text
            else:
                text += SWKBD_MAP[kbdMode][kbdSelection]

        kbdMode %= len(SWKBD_MAP)
        if kbdSelection < 0:
            kbdSelection = 40 + kbdSelection
        kbdSelection %= 40

def msgBox(title, text):
    renderMessageBox(title, text)
    waitKey()

def showMenu(items, caption, selectTo=None):
    itemPerPage = SCREEN_H / (itemHeight) - 2
    selBorder = 4
    menuRect = (0, basicFontHeight, SCREEN_W, SCREEN_H - basicFontHeight * 2)
    menuSel = 0

    if len(items) == 0:
        renderMessageBox(caption, '-- No Items --')
        key = waitKey()
        return -1, None

    if selectTo != None:
        if selectTo >= 0:
            menuSel = selectTo
    while True:
        if (menuSel >= len(items)):
            menuSel = 0
        if (menuSel < 0):
            menuSel = len(items) - 1
        menuStart = (menuSel / itemPerPage) * itemPerPage
        clearAndDrawTitle(caption)
        x = 30
        y = itemHeight

        for i in range(menuStart, min(menuStart + itemPerPage, len(items))):
            drawText(x, y + 10, items[i], COLOR_FG, COLOR_BG)
            if menuSel == i:
                drawBorder(0, y, SCREEN_W, itemHeight,
                           selBorder, COLOR_MENU_SEL)
            screen.fill(COLOR_LINE, (0, y + itemHeight - 1, SCREEN_W, 1))
            y += itemHeight
        drawText(SCREEN_W - 200, y + 10, 'Page %d/%d' % (menuSel / itemPerPage +
                                                         1, (len(items) - 1) / itemPerPage + 1), COLOR_FG, COLOR_BG)
        updateScreen()

        key = waitKey()
        if (key == K_DOWN):
            menuSel += 1
        elif key == K_UP:
            menuSel -= 1
        elif (key == K_RETURN) or (key == K_RIGHT) or (key == K_LEFT) or (key == K_SPACE):
            return menuSel, key
        elif key == K_ESCAPE:
            return -1, key
        elif key == K_F1:
            handlePowerButton()


def playVideoMenu():
    fullPathList = []
    fileNameList = []
    try:
        os.mkdir(VIDEO_PATH)
    except:
        pass
    for root, dirs, files in os.walk(VIDEO_PATH):
        for name in files:
            if name.endswith(".mkv") or name.endswith(".mp4"):
                if not name.startswith('.'):
                    fullPath = os.path.join(root, name)
                    fullPathList.append(fullPath)
                    fileNameList.append(name.decode('utf-8'))
    while True:
        ret, event = showMenu(fileNameList, "Select File")
        if ret < 0:
            return
        path = fullPathList[ret]
        srtPath = path.rsplit('.', 1)[0] + '.srt'
        if os.path.isfile(srtPath):
            print('Srt file found: ' + srtPath)
        else:
            srtPath = None
        callOMXPlayer(path, srtPath)


def tvMenu():
    tvTitleList = []
    tvUrlList = []
    content = u''
    try:
        with open('/disk/tv.txt', 'r') as f:
            content = f.read().decode('utf-8')
    except:
        pass
    for line in content.split(u'\n'):
        arr = line.strip().split(',', 1)
        if len(arr) == 2:
            tvTitleList.append(arr[0])
            tvUrlList.append(arr[1])
    while True:
        ret, event = showMenu(tvTitleList, "TV")
        if ret < 0:
            return
        callOMXPlayer(tvUrlList[ret], mode='tv')


def projectorMenu():
    global projectorArgValue
    ret = -1
    while True:
        menu = []
        for i in range(0, 9):
            title, l, r, cmd = PROJECTOR_ARGS[i]
            menu.append('%s = %d' % (title, projectorArgValue[i]))
        menu += ['Save settings', 'Restore settings']
        ret, event = showMenu(menu, 'Projector Control', selectTo=ret)
        if ret == -1:
            return
        if ret < 9:
            title, l, r, cmd = PROJECTOR_ARGS[ret]
            if event == K_LEFT:
                projectorArgValue[ret] -= 1
            if event == K_RIGHT:
                projectorArgValue[ret] += 1
            projectorArgValue[ret] = max(l, min(r, projectorArgValue[ret]))
            if ret <= 4:
                cmd = '\xff\x07' + \
                    chr(cmd) + struct.pack('b',
                                           projectorArgValue[ret]) + '\x00' * 3
            else:
                index = 5 + ((ret - 5) / 2 * 2)
                cmd = '\xff\x07' + chr(cmd) + struct.pack(
                    'bb', projectorArgValue[index],  projectorArgValue[index + 1]) + '\x00' * 2
            submitSerialCommand(cmd)
        if ret == 9:
            submitSerialCommand('\xff\x07\x0b\x00\x00\x00\x00')
        if ret == 10:
            submitSerialCommand('\xff\x07\x77\x00\x00\x00\x00')
            projectorArgValue = [0] * 9


def powerMenu():
    ret, event = showMenu(
        ['Shutdown', 'Return to shell', 'Update'], 'Power options')
    if ret == 0:
        with open('/run/next', 'w') as f:
            f.write('poweroff;exit')
        serial.write(CMD_TOGGLE_POWER + '\xa0')
        time.sleep(5)
        sys.exit()
    if ret == 1:
        with open('/run/next', 'w') as f:
            f.write('exit')
        sys.exit()
    if ret == 2:
        with open('/run/next', 'w') as f:
            f.write('source /disk/update/update.sh')
        sys.exit()


def setWiFiNetwork(ssid, pwd):
    WPA_CLI_CMD = ['wpa_cli', '-i' ,'wlan0' ]

    ret = runCommandAndGetOutput(WPA_CLI_CMD + ['remove_network', 'all'])
    if ssid != '':
        ret = runCommandAndGetOutput(WPA_CLI_CMD + ['add_network'])
        networkID = ret.strip()
        print('networkID', networkID)
        ret = runCommandAndGetOutput(WPA_CLI_CMD + ['set_network', networkID, 'ssid', '"%s"' % (ssid)])
        if pwd == '':
            ret = runCommandAndGetOutput(WPA_CLI_CMD + ['set_network', networkID, 'key_mgmt', 'NONE'])
        else:
            ret = runCommandAndGetOutput(WPA_CLI_CMD + ['set_network', networkID, 'psk', '"%s"' % (pwd)])
        ret = runCommandAndGetOutput(WPA_CLI_CMD + ['enable_network', networkID])
    ret = runCommandAndGetOutput(WPA_CLI_CMD + ['save_config'])


def configMenu():
    
    ret, event = showMenu(
        ['WiFi', 'System Info'], 'Settings'
    )
    if ret == 0:
        pwd = None
        ssid = inputDialog('WiFi SSID', '')
        if ssid != None:
            pwd = inputDialog('WiFi Password', '')
        if (ssid == None) or (pwd == None) or ((ssid == '') and (pwd != '')):
            msgBox('WiFi', 'WiFi config cancelled.')
            return
        setWiFiNetwork(ssid, pwd)
        if ssid == '':
            msgBox('WiFi', 'WiFi config cleared.')
        else:
            msgBox('WiFi', 'WiFi config saved.')
    elif ret == 1:
        msgBox('System Info', 'IP: %s' % (runCommandAndGetOutput(['hostname', '-I']).strip()))




def dlnaMenu():
    mediarenderer.currentURI = None
    while True:
        renderMessageBox('DLNA', 'Waiting...')
        key = waitKey(500)
        if key == K_ESCAPE:
            return
        if (mediarenderer.currentURI != None):
            uri = mediarenderer.currentURI
            callOMXPlayer(uri, mode='dlna')
            mediarenderer.currentURI = None


mediarenderer.startHTTPServer()
mediarenderer.startSSDPService()

while True:
    ret, event = showMenu(
        ["Play Video", "TV", "DLNA", "Projector Control", "Settings", "Power options"], "Main")
    if ret == 0:
        playVideoMenu()
    elif ret == 1:
        tvMenu()
    elif ret == 2:
        dlnaMenu()
    elif ret == 3:
        projectorMenu()
    elif ret == 4:
        configMenu()
    elif ret == 5:
        powerMenu()
