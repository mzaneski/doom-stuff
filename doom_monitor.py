import threading
import time

class T_DoomMonitor(threading.Thread):
    def __init__(self, file, queue, interval=1.0):
        assert callable(file.readline)
        threading.Thread.__init__(self)

        self.file = file
        self.queue = queue
        self.interval = interval

        self.abort = False

        self.players = {}

    def run(self):
        timestamp = 0

        for l in iter(self.file.readline, ''):
            if self.abort:
                break

            line = l.decode('ascii').strip()

            if line.startswith('CHAT'):
                self.queue.append(line[5:])
            elif line.endswith('disconnected.'):
                pname = line[7:line.find(' ', 7)]
                if pname in self.players:
                    del self.players[pname]
                self.queue.append('{} stopped playing Doom.'.format(pname))
            elif line.endswith('has connected.'):
                pname = line[:line.find(' ')]
                self.players[pname] = None
                self.queue.append('{} is now playing Doom!'.format(pname))
            else:
                for pname in self.players:
                    if pname in line.split(' '):
                        self.queue.append(line)

            time.sleep(self.interval)

    def stop_monitoring(self):
        self.abort = True

    def eof(self):
        return not self.is_alive() and not self.queue
