import subprocess
import socket
import time

def runCommandAndGetOutput(args):
    print('runCommand', args)
    ret = subprocess.check_output(args)
    print(ret)
    return ret.decode('utf-8')

def runCommandAndGetOutputWithStdin(args, input):
    proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write(input.encode('utf-8'))
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait()
    return proc.stdout.read().decode('utf-8')


def getMyIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def logWithTimestamp(msg):
    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + ' ' + msg)