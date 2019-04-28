import subprocess
import time

from collections import deque

from doom_monitor import T_DoomMonitor

def get_logger_pid():
    proc = subprocess.Popen('./utils/get_logger_pid.sh',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = proc.communicate(timeout=5)
    PID = out.decode('ascii').strip()
    if proc.poll() is None:
        proc.kill()

    if PID.isspace() or not PID.isdigit():
        return None
    else:
        return PID

def listen_for_server(pid_method, wait_time=10.0):
    assert callable(pid_method)

    PID = pid_method()
    while not PID:
        time.sleep(wait_time)
        PID = pid_method()

    monitor_server(PID)

def monitor_server(PID, wait_time=1.0):
    cmd = ['tail', '-f', '-n', '1', '--pid={}'.format(PID), '/proc/{}/fd/1'.format(PID)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    out_q = deque()
    reader = T_DoomMonitor(proc.stdout, out_q, interval=wait_time)

    try:
        reader.start()

        while not reader.eof():
            while out_q:
                line = out_q.popleft()
                print(line)

            if not proc.poll() is None and reader.is_alive():
                reader.stop_monitoring()

            time.sleep(wait_time)
    except KeyboardInterrupt:
        raise
    finally:
        if reader.is_alive() and not reader.abort:
            reader.stop_monitoring()
        time.sleep(wait_time)
        reader.join()
        proc.stdout.close()

        if proc.poll() is None:
            proc.kill()

if __name__ == '__main__':
    while(True):
        listen_for_server(get_logger_PID)
