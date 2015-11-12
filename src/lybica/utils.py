import subprocess
import sys


def execute_command(*cmds):
    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while p.poll() is None:
        sys.stdout.write(p.stdout.readline())
        sys.stdout.flush()

    while True:
        buff = p.stdout.read(1024)
        if not buff:
            break
        sys.stdout.write(buff)
        sys.stdout.flush()

    return p.returncode

