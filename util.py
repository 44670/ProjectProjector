import subprocess

def runCommandAndGetOutput(args):
    print('runCommand', args)
    ret = subprocess.check_output(args)
    print(ret)
    return ret

def runCommandAndGetOutputWithStdin(args, input):
    proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write(input)
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait()
    return proc.stdout.read()
