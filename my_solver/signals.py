import psutil
import sys
import os

def handler(signum, frame):
    print("signum {}".format(signum))
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        print("Child pid is {}\n".format(child.pid))
        print("Killing child.")
        try:
            os.kill(child.pid, 15)
        except OSError as e:
            print("Process might already be gone. See error below.")
            print(e)

    print("SIGNAL received")
    if signum == 15:
        raise TimeoutError("signal")
    else:
        raise InterruptedError("signal")

def nothing(signum, frame):
    print("SIGNAL received\n")
    print("SIGNAL ignored...\n")
