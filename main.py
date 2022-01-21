import sys
sys.path.append(".")
import proj

from ui import *
import mediarenderer
import ota
import subprocess
from util import *
import bl
import json
import os
from const import *
import calib

mediarenderer.startSSDPService()
mediarenderer.startHTTPServer()

config = {}

def loadConfig():
    global config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        for k in DEFAULT_CONFIG.keys():
            if not (config.has_key(k)):
                config[k] = DEFAULT_CONFIG[k]
    except Exception as e:
        print('load config failed... use default config')
        print(e)
        config = DEFAULT_CONFIG.copy()

def saveConfig():
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

loadConfig()

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
    elif bl.blTryConfigureAudio():
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
            ota.installPayload(fullPath)
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
        ['Video Player', 'WiFi', 'Network Info', 'System Info', 'Software Update'], 'Settings'
    )
    if ret == 0:
        videoPlayerConfigMenu()
    elif ret == 1:
        pwd = None
        ssid = inputDialog('WiFi SSID', '')
        if (ssid == '9527'):
            import calib
            calib.calib()
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
        msgBox('System Info', 'Version: v%d\nSN: %s' % (VERSION_CODE, ota.getSerial()))
    elif ret == 4:
        ota.checkUpdate()

def powerMenu():
    ret, event = showMenu(
        ['Shutdown','Reboot', 'Return to shell'], 'Power options')
    if ret == 0:
        with open('/run/next', 'w') as f:
            f.write('poweroff;exit')
        sys.exit()
    if ret == 1:
        with open('/run/next', 'w') as f:
            f.write('reboot;exit')
        sys.exit()
    if ret == 2:
        with open('/run/next', 'w') as f:
            f.write('exit')
        sys.exit()

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
        calib.calib()
        projectorMenu()
    elif ret == 4:
        bl.blMenu()
    elif ret == 5:
        configMenu()
    elif ret == 6:
        powerMenu()

