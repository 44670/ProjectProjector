#!/usr/bin/env python3

castServEnabled = True

import subprocess
import json
import threading
import os
import time

currentURI = None

def CastServThread():
    os.system("killall ProjectCast")
    while True:
        time.sleep(5)
        if not castServEnabled:
            print('ProjectCast disabled, byebye')
            return
        proc = subprocess.Popen(['/opt/shell/ProjectCast', '-name', 'MyProjector'], stdout=subprocess.PIPE)
        while proc.poll() is None:
            out = proc.stdout.readline().strip()
            print('ProjectCast: ' , out)
            if len(out) < 1:
                continue
            if out[0] == b'[':
                try:
                    data = json.loads(out)
                    if data[0] in ['play', 'dlna-play']:
                        currentURI = data[1]
                        print('ProjectCast: currentURI: ' + currentURI)
                except Exception as e:
                    print('ProjectCast: JSON error: ' + str(e))
                    continue
        print('ProjectCast exits, restart...')


def start():
    castServThread = threading.Thread(target=CastServThread)
    castServThread.daemon = True
    castServThread.start()

