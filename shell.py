# -*- coding: utf-8 -*-
from pygame.locals import *
from gpiozero import Button
import struct
import binascii
import pygame.freetype
import pygame.image
import pygame
import subprocess
import time
import sys
import os
import serial
import json
import urllib2
import zipfile
import hashlib
import threading

import mediarenderer

from lang_cn import TR


VERSION_CODE = 20210602
VERSION = 'v%s' % VERSION_CODE

BASE_PATH = '/opt/shell/'
VIDEO_PATH = '/disk/video'
CONFIG_PATH = '/opt/shell/config.json'
FONT_PATH = '/opt/shell/font.ttf'
MOUNT_DISK_CMD = 'mount /dev/mmcblk0p3 /disk -o nonempty'


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

LED_BASEDIR = '/sys/class/leds/led0/'
ledCounter = 0

otaJson = None
otaZipFile = None

config = {}

defaultConfig = {
            'DefaultVideoDelay':0,
            'DefaultVideoDelayBluetooth':-600,
            'DefaultVolume':-12,
            'AlsaVolume':70,
            'DistortionUpDown': 30,
            'DistortionLeftRight': 30
        }

def loadConfig():
    global config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        for k in defaultConfig.keys():
            if not (config.has_key(k)):
                config[k] = defaultConfig[k]
    except Exception as e:
        print('load config failed... use default config')
        print(e)
        config = defaultConfig.copy()

def saveConfig():
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

loadConfig()

def tryWriteFile(fn, data):
    try:
        with open(fn, 'wb') as f:
            f.write(data)
    except Exception as e:
        print(e)

tryWriteFile(LED_BASEDIR + 'trigger', 'none')

def ledThreadLoop():
    global ledCounter
    while True:
        time.sleep(1)
        if ledCounter > 0:
            ledCounter -= 1
            if ledCounter == 0:
                tryWriteFile(LED_BASEDIR + 'brightness', '1')

def setLedOn(offAfterSeconds):
    global ledCounter
    tryWriteFile(LED_BASEDIR + 'brightness', '0')
    ledCounter = offAfterSeconds
    

ledThread = threading.Thread(target=ledThreadLoop)
ledThread.daemon = True
ledThread.start()

setLedOn(60)

def otaGetSerial():
    with open('/proc/cpuinfo','rb') as f:
        info = f.read()
        for line in info.split('\n'):
            if line.startswith('Serial'):
                return (line.split(':')[1].strip())
    return 'unknown'

def getFileSha256Hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            buf = f.read(256 * 1024)
            if buf == '':
                break
            h.update(buf)
        return h.hexdigest()

def otaUrlOpen(url):
    print(url)
    req = urllib2.Request(url, headers={ 'User-Agent': '44IoT' })
    return urllib2.urlopen(req)



def otaInstallPayload(path):
    global castServEnabled
    castServEnabled = False
    os.system('killall CastService bluealsa omxplayer.bin')
    time.sleep(1)
    global otaZipFile
    otaZipFile = zipfile.ZipFile(path)
    exec(otaZipFile.read('update.py'))

def otaStartUpdate():
    global otaJson
    updateZipPath = '/root/update.zip'
    f = otaUrlOpen(otaJson['file'])
    with open(updateZipPath, 'wb') as outf:
        bytesDownloaded = 0
        while True:
            data = f.read(64 * 1024)
            if len(data) <= 0:
                break
            outf.write(data)
            bytesDownloaded += len(data)
            renderMessageBox('Software Update', TR('Downloading update package(%d KiB)...') % (bytesDownloaded / 1024))
    if getFileSha256Hash(updateZipPath) != otaJson['hash']:
        msgBox('Software Update', 'Update package verification failed.')
        return
    otaInstallPayload(updateZipPath)

def otaCheckUpdate():
    global otaJson, otaZipFile
    otaJson = None
    otaZipFile = None
    renderMessageBox('Software Update', 'Checking update...',)
    try:
        f = otaUrlOpen('https://44670.org/ota/ota.json?sn=%s&v=%d' % (otaGetSerial(), VERSION_CODE))
        otaJson = json.loads(f.read()) 
    except Exception as e:
        print(e)
        msgBox('Software Update', 'Check update failed.')
        return
    if otaJson['versionCode'] <= VERSION_CODE:
        msgBox('Software Update', 'Your software is up to date.')
        return
    menu = ['>Update Later', '>Update Now', TR('New version: ') + otaJson['version']]
    for line in otaJson['message'].split('\n'):
        menu.append(line)
    ret, event = showMenu(menu, 'Software update is available.')
    if ret == 1:
        otaStartUpdate()

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
        renderMessageBox('Please wait...', 'Standby')
        setLedOn(60)
        time.sleep(20)
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

laserImg = None
laserImg = pygame.image.load(BASE_PATH + 'laser.png')


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
    useBluealsa = False
    screen.fill(COLOR_BG)
    updateScreen()

    aplayRet = runCommandAndGetOutput(['aplay', '-l'])
    args = ['/usr/bin/omxplayer.bin']
    args += ['--win', '0,0,%d,%d' % (SCREEN_W, SCREEN_H)]
    if (aplayRet.find('card 1:') != -1):
        print('Using usb sound card...')
        args += ['-o', 'alsa:hw:1,0']
    elif blTryConfigureAudio():
        useBluealsa = True
        args += ['-o', 'alsa:bluealsa']
    else:
        args += ['-o', 'local']
    args += ['--font', FONT_PATH, '--italic-font', FONT_PATH]
    args += ['--timeout', '120']
    args += ['--vol', '%d' % (config['DefaultVolume'] * 100)]
    videoDelay = int(config['DefaultVideoDelay'])
    if useBluealsa:
        videoDelay = config['DefaultVideoDelayBluetooth']
    args += ['--video-delay', '%d' % videoDelay]
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
        elif key == K_4:
            proc.stdin.write('3')
            proc.stdin.flush()
        elif key == K_6:
            proc.stdin.write('4')
            proc.stdin.flush()
        

    return None


def handlePowerButton():
    print('---power button pressed---')
    submitSerialCommand(CMD_TOGGLE_POWER)


def updateScreen():
    pygame.display.update()


def drawText(x, y, text, colorFg, colorBg):
#    if not isinstance(text, unicode):
#        text = text.decode('utf-8')
    return basicFont.render_to(screen, (x, y), text, colorFg, colorBg)

def drawTextMultiline(x, y, text, colorFg, colorBg):
#    if not isinstance(text, unicode):
#        text = text.decode('utf-8')
    for line in text.split(u'\n'):
        basicFont.render_to(screen, (x, y), line, colorFg, colorBg)
        y += itemHeight


def clearAndDrawTitle(title):
    screen.fill(COLOR_BG)
    screen.fill(COLOR_FG, (0, itemHeight - 3, SCREEN_W, 2))
    drawText(10, 5, title, COLOR_FG, COLOR_BG)


def renderMessageBox(title, msg):
    clearAndDrawTitle(TR(title))
    drawTextMultiline(30, itemHeight + 10, TR(msg), COLOR_FG, COLOR_BG)
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
        clearAndDrawTitle(TR(title))
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

def drawWarning(x=0, y=0):
    screen.blit(laserImg, (x, y))
    x += 160
    basicFont.render_to(screen, (x, y), u'警告：本设备为Class 3R激光设备，错误使用可能导致永久性视力损害。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'请勿直视本设备发出的激光光束，更不能将激光指向自己或其他人。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'儿童必须在家长监护下使用本设备。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'机身绿色指示灯亮时请勿移除电源。', COLOR_FG, COLOR_BG, size=35)

def showMenu(items, caption, selectTo=None, style=None):
    caption = TR(caption)

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
            drawText(x, y + 10, TR(items[i]), COLOR_FG, COLOR_BG)
            if menuSel == i:
                drawBorder(0, y, SCREEN_W, itemHeight,
                           selBorder, COLOR_MENU_SEL)
            screen.fill(COLOR_LINE, (0, y + itemHeight - 1, SCREEN_W, 1))
            y += itemHeight

        if len(items) > itemPerPage:
            drawText(SCREEN_W - 200, y + 10, 'Page %d/%d' % (menuSel / itemPerPage +
                                                         1, (len(items) - 1) / itemPerPage + 1), COLOR_FG, COLOR_BG)
        if style == 'main':
            drawWarning(10, 530)
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
        ['Shutdown', 'Return to shell', 'Install Package'], 'Power options')
    if ret == 0:
        with open('/run/next', 'w') as f:
            f.write('poweroff;exit')
        setLedOn(60)
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

def udiskMode():
    os.system('umount /disk')
    os.system('modprobe g_mass_storage file=/dev/mmcblk0p3 stall=0 removable=1')
    while True:
        renderMessageBox('USB File Transfer', 'Connect to PC via the right micro-usb port.')
    
        key = waitKey(500)
        if key == K_ESCAPE:
            break
    os.system('sync')
    os.system('rmmod g_mass_storage')
    os.system('sync')
    os.system(MOUNT_DISK_CMD)

def videoPlayerConfigMenu():
    menu = ['', '', '']
    ret = -1
    while True:
        menu[0] = TR('Default Volume: %d dB') % config['DefaultVolume']
        menu[1] = TR('Default Video Delay: %d') % config['DefaultVideoDelay']
        menu[2] = TR('Default Video Delay for Bluetooth: %d') % config['DefaultVideoDelayBluetooth']
        ret, event = showMenu(menu, 'Video Player', selectTo=ret)
        d = 0
        if event == K_RIGHT:
            d = 1
        elif event == K_LEFT:
            d = -1
        if ret < 0:
            saveConfig()
            return
        elif ret == 0:
            config['DefaultVolume'] += d
        elif ret == 1:
            config['DefaultVideoDelay'] += 10 * d
        elif ret == 2:
            config['DefaultVideoDelayBluetooth'] += 10 * d

def configMenu():
    
    ret, event = showMenu(
        ['Video Player', 'WiFi', 'Network Info', 'System Info', 'Software Update', '<!> Format Internal Storage'], 'Settings'
    )
    if ret == 0:
        videoPlayerConfigMenu()
    elif ret == 1:
        pwd = None
        ssid = inputDialog('WiFi SSID', '')
        if (ssid == '9527'):
            with open('/run/next', 'w') as f:
                f.write('python /opt/shell/calib.py')
            sys.exit()
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
    elif ret == 2:
        msgBox('Network Info', 'IP: %s' % (runCommandAndGetOutput(['hostname', '-I']).strip()))
    elif ret == 3:
        msgBox('System Info', 'Version: v%d\nSN: %s' % (VERSION_CODE, otaGetSerial()))
    elif ret == 4:
        otaCheckUpdate()
    elif ret == 5:
        msg = inputDialog('Enter "OK" to DELETE ALL DATA.', '')
        if msg == 'OK':
            os.system('umount /disk')
            os.system('blkdiscard /dev/mmcblk0p3')
            os.system('parted /dev/mmcblk0 < /opt/shell/parted.ans')
            os.system('mkfs.exfat -s 2048 /dev/mmcblk0p3')
            os.system('sync')
            os.system('fdisk /dev/mmcblk0 < /opt/shell/fdisk.ans')
            os.system(MOUNT_DISK_CMD)
            os.system('mkdir /disk/video /disk/game')
            os.system('sync')
            msgBox('Format', 'Done')
        else:
            msgBox('Format', 'Format cancelled.')

def dlnaMenu():
    ip = (runCommandAndGetOutput(['hostname', '-I']).strip())
    mediarenderer.currentURI = None
    while True:
        renderMessageBox('Wireless Casting', TR('Waiting...\nhttp://%s') % ip)
        key = waitKey(500)
        if key == K_ESCAPE:
            return
        if (mediarenderer.currentURI != None):
            uri = mediarenderer.currentURI
            callOMXPlayer(uri, mode='dlna')
            mediarenderer.currentURI = None

def fileBrowser(dir):
    fnList = os.listdir(dir)
    while True:
        unicodeFnList = []
        for fn in fnList:
            unicodeFnList.append(fn.decode('utf-8'))
        ret, event = showMenu(unicodeFnList, dir)
        if ret < 0:
            return
        fullPath = dir + '/' + fnList[ret]
        if os.path.isdir(fullPath):
            fileBrowser(fullPath)
        elif fullPath.lower().endswith('.swupd'):
            otaInstallPayload(fullPath)
        else:
            srtPath = fullPath.rsplit('.', 1)[0] + '.srt'
            if os.path.isfile(srtPath):
                print('Srt file found: ' + srtPath)
            else:
                srtPath = None
            callOMXPlayer(fullPath, srtPath)

    

def fileMenu():
    ret, event = showMenu(['Internal Storage', 'UDisk'], 'Select Device')
    if ret == 0:
        fileBrowser('/disk')
    elif ret == 1:
        try:
            os.mkdir('/udisk')
        except:
            pass
        os.system('mount /dev/sda1 /udisk')
        os.system('mount /dev/sda /udisk')
        fileBrowser('/udisk')
        os.system('umount /udisk')

# Bluetooth

def blGetCurrentConnectedAudioAddr():
    ret = runCommandAndGetOutput(['bluealsa-aplay', '-L']).split('DEV=')
    if len(ret) <= 1:
        return None
    return ret[1].split(',', 1)[0]

def blTryConfigureAudio():
    flushKey()
    addr = blGetCurrentConnectedAudioAddr()
    if addr is None:
        pairedDevices = blGetDevices(True)
        if len(pairedDevices) <= 0:
            return False
        pairedAddr, pairedName = pairedDevices[0]
        for retry in range(0, 3):
            renderMessageBox('Bluetooth', 'Connecting bluetooth audio device...')
            blStartConnectDevice(pairedAddr)
            key = waitKey(5000)
            addr = blGetCurrentConnectedAudioAddr()
            if not(addr is None):
                break
            if key == K_ESCAPE:
                # Skip retrying if escape pressed
                break
        if addr is None:
            msgBox('Bluetooth', 'Failed to connect bluetooth audio device.\nFallback to 3.5mm output.')
            flushKey()
    if addr is None:
        return False
    with open('/root/.asoundrc', 'w') as f:
        f.write("""defaults.bluealsa.device "%s"
defaults.bluealsa.profile "a2dp"
defaults.bluealsa.delay 40000""" % (addr))
    return True



def runCommandAndGetOutputWithStdin(args, input):
    proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write(input)
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait()
    return proc.stdout.read()

def blCallBluetoothCtl(cmd):
    return runCommandAndGetOutputWithStdin(['bluetoothctl'], cmd + '\n')



def blGetDevices(pairedOnly = False):
    ret = []
    cmd = 'devices'
    if pairedOnly:
        cmd = 'paired-devices'
    lines = blCallBluetoothCtl(cmd).split('\n')
    for line in lines:
        if line.startswith('Device '):
            tmp = line.split(' ', 2)
            if len(tmp) < 2:
                continue
            deviceName = ''
            deviceAddr = tmp[1]
            if len(tmp) >= 3:
                deviceName = tmp[2]
            ret.append((deviceAddr, deviceName))
    return ret

blScanProc = None

def blStopScan():
    global blScanProc
    if blScanProc is None:
        return
    blScanProc.stdin.close()
    blScanProc.wait()
    blScanProc = None

def blStartScan():
    global blScanProc
    blStopScan()
    blScanProc = subprocess.Popen(args=['bluetoothctl'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    blScanProc.stdin.write('set-scan-filter-transport bredr\n')
    blScanProc.stdin.write('scan on\n')
    blScanProc.stdin.flush()

def blStartConnectDevice(addr):
    blCallBluetoothCtl('connect ' + addr)
    
def blPairDevice(addr):
    global blScanProc
    blScanProc.stdin.write('pair %s\n' % addr);blScanProc.stdin.flush()
    time.sleep(3)
    isPaired = False
    for retry in range(0, 10):
        pairedDevices = blGetDevices(True)
        for paddr, pname in pairedDevices:
            if paddr == addr:
                isPaired = True
                break 
        if isPaired:
            break
        time.sleep(5)
    time.sleep(5)
    blCallBluetoothCtl('trust ' + addr)
    blCallBluetoothCtl('connect ' + addr)
    return isPaired


def blRemoveDevice(addr):
    blCallBluetoothCtl('remove ' + addr)


def blMenu():
    pairedDevices = blGetDevices(True)

    menu = ['Add Device']
    if len(pairedDevices) > 0:
        menu[0] = 'Remove Device'
        menu.append('---Paired Devices---')
        for addr, name in pairedDevices:
            menu.append((addr + ' ' + name).decode('utf-8'))
    ret, event = showMenu(menu, 'Bluetooth')
    if ret == 0:
        if len(pairedDevices) > 0:
            msgBox('Bluetooth', 'Device is removed.')
            for addr, name in pairedDevices:
                blRemoveDevice(addr)
        else:
            renderMessageBox('Scanning', 'Please wait...')
            blStartScan()
            time.sleep(15)
            scannedDevices = blGetDevices(False)
            menu2 = []
            for addr, name in scannedDevices:
                menu2.append((addr + ' ' + name).decode('utf-8'))
            ret2, event2 = showMenu(menu2, 'Devices Found')
            if ret2 >= 0:
                addr, name = scannedDevices[ret2]
                renderMessageBox('Bluetooth', 'Pairing...')
                isPaired = blPairDevice(addr)
                if isPaired:
                    msgBox('Bluetooth', 'Device is paired.')
                else:
                    msgBox('Bluetooth', 'Failed to pair device.')
            blStopScan()


# Main loop

os.system(MOUNT_DISK_CMD)
mediarenderer.startHTTPServer()
mediarenderer.startSSDPService()
castServEnabled = True
def CastServThread():
    os.system('killall CastService')
    while True:
        time.sleep(5)
        if not castServEnabled:
            print('CastService disabled, byebye')
            return
        proc = subprocess.Popen(['/opt/shell/CastService'], stdout=subprocess.PIPE)
        while proc.poll() is None:
            out = proc.stdout.readline().strip()
            print('CastService: ' + out)
            if len(out) < 1:
                continue
            if out[0] == '!':
                arr = out.split('!', 2)
                if len(arr) >= 3:
                    if arr[1] == 'play':
                        mediarenderer.currentURI = arr[2]
        print('CastService exits, restart...')

castServThread = threading.Thread(target=CastServThread)
castServThread.daemon = True
castServThread.start()

while True:
    ret, event = showMenu(
        ["Files", "TV", "Wireless Casting", "Projector Control", "Bluetooth", "Settings", "Power options"], "Main", style='main')
    if ret == 0:
        fileMenu()
    elif ret == 1:
        tvMenu()
    elif ret == 2:
        dlnaMenu()
    elif ret == 3:
        projectorMenu()
    elif ret == 4:
        blMenu()
    elif ret == 5:
        configMenu()
    elif ret == 6:
        powerMenu()

