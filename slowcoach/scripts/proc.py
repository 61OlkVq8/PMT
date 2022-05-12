import psutil
import signal
import os


def cleanExpieredProcess(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)
        try:
            os.waitpid(process.pid, 0)
        except ChildProcessError:
            pass
    parent.send_signal(sig)
    try:
        os.waitpid(parent_pid, 0)
    except ChildProcessError:
        pass
