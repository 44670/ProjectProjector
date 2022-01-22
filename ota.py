import urllib
import os
import hashlib
import zipfile
import json
import time

import ui
from const import *

import cast

def getSerial():
    if os.name == 'nt':
        return 'unknown'
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

def urlOpen(url):
    print(url)
    req = urllib.Request(url, headers={ 'User-Agent': '44IoT' })
    return urllib.urlopen(req)

def installPayload(path):
    cast.castServEnabled = False
    os.system('killall ProjectCast bluealsa omxplayer.bin')
    time.sleep(1)
    global otaZipFile
    otaZipFile = zipfile.ZipFile(path)
    exec(otaZipFile.read('update.py'))

def startUpdate():
    global otaJson
    updateZipPath = '/root/update.zip'
    f = urlOpen(otaJson['file'])
    with open(updateZipPath, 'wb') as outf:
        bytesDownloaded = 0
        while True:
            data = f.read(64 * 1024)
            if len(data) <= 0:
                break
            outf.write(data)
            bytesDownloaded += len(data)
            ui.renderMessageBox('Software Update', ui.TR('Downloading update package(%d KiB)...') % (bytesDownloaded / 1024))
    if getFileSha256Hash(updateZipPath) != otaJson['hash']:
        ui.msgBox('Software Update', 'Update package verification failed.')
        return
    installPayload(updateZipPath)
    
def checkUpdate():
    global otaJson, otaZipFile
    otaJson = None
    otaZipFile = None
    ui.renderMessageBox('Software Update', 'Checking update...',)
    try:
        f = urlOpen('https://ota.44670.org/proj2/ota.json?sn=%s&v=%d' % (getSerial(), VERSION_CODE))
        otaJson = json.loads(f.read()) 
    except Exception as e:
        print(e)
        ui.msgBox('Software Update', 'Check update failed.')
        return
    if otaJson['versionCode'] <= VERSION_CODE:
        ui.msgBox('Software Update', 'Your software is up to date.')
        return
    menu = ['>Update Later', '>Update Now', ui.TR('New version: ') + otaJson['version']]
    for line in otaJson['message'].split('\n'):
        menu.append(line)
    ret, event = ui.showMenu(menu, 'Software update is available.')
    if ret == 1:
        startUpdate()
