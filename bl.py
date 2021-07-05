import ui
import util
import time
import subprocess

def blTryConfigureAudio():
    ui.flushKey()
    addr = blGetCurrentConnectedAudioAddr()
    if addr is None:
        pairedDevices = blGetDevices(True)
        if len(pairedDevices) <= 0:
            return False
        pairedAddr, pairedName = pairedDevices[0]
        for retry in range(0, 3):
            ui.renderMessageBox('Bluetooth', 'Connecting bluetooth audio device...')
            blStartConnectDevice(pairedAddr)
            key = ui.waitKey(5000)
            addr = blGetCurrentConnectedAudioAddr()
            if not(addr is None):
                break
            if key == ui.K_ESCAPE:
                # Skip retrying if escape pressed
                break
        if addr is None:
            ui.msgBox('Bluetooth', 'Failed to connect bluetooth audio device.\nFallback to 3.5mm output.')
            ui.flushKey()
    if addr is None:
        return False
    with open('/root/.asoundrc', 'w') as f:
        f.write("""defaults.bluealsa.device "%s"
defaults.bluealsa.profile "a2dp"
defaults.bluealsa.delay 40000""" % (addr))
    return True

def blCallBluetoothCtl(cmd):
    return util.runCommandAndGetOutputWithStdin(['bluetoothctl'], cmd + '\n')

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
    ret, event = ui.showMenu(menu, 'Bluetooth')
    if ret == 0:
        if len(pairedDevices) > 0:
            ui.msgBox('Bluetooth', 'Device is removed.')
            for addr, name in pairedDevices:
                blRemoveDevice(addr)
        else:
            ui.renderMessageBox('Scanning', 'Please wait...')
            blStartScan()
            time.sleep(15)
            scannedDevices = blGetDevices(False)
            menu2 = []
            for addr, name in scannedDevices:
                menu2.append((addr + ' ' + name).decode('utf-8'))
            ret2, event2 = ui.showMenu(menu2, 'Devices Found')
            if ret2 >= 0:
                addr, name = scannedDevices[ret2]
                ui.renderMessageBox('Bluetooth', 'Pairing...')
                isPaired = blPairDevice(addr)
                if isPaired:
                    ui.msgBox('Bluetooth', 'Device is paired.')
                else:
                    ui.msgBox('Bluetooth', 'Failed to pair device.')
            blStopScan()

def blGetCurrentConnectedAudioAddr():
    ret = util.runCommandAndGetOutput(['bluealsa-aplay', '-L']).split('DEV=')
    if len(ret) <= 1:
        return None
    return ret[1].split(',', 1)[0]