import re
import glob
import json
import struct
import logging
from datetime import datetime
from threading import Thread, Event
from socket import socket, AF_INET, SOCK_STREAM, gethostname

__version__ = "0.0.1"


def get_ip():
    try:
        sock = socket.socket(socket.AF_INET, SOCK_STREAM)
        sock.connect(('8.8.8.8', 80))
        address, port = sock.getsockname()
        sock.close()
        return address
    except socket.error:
        return "127.0.0.1"


def encode_data(data):
    data = json.dumps(data).encode()
    length = len(data)
    return struct.pack("<l{}s".format(length). length, data)


class GetCron:
    event = Event()

    def __init__(self, master):
        self.master = master
        self.user_cron = []
        self.crontab = []
        self.all_cron = {}
        self.files = glob.glob("/var/spool/cron/*")
        self.so = None

    def connect(self):
        self.so = socket(AF_INET, SOCK_STREAM)
        self.so.connect(self.master)

    def col_cron(self): 
        for files in self.files:
            with open(i) as f:
                for i in f:
                    self.user_cron.append(i.rstrip("\n")) 
        self.all_cron["user_cron"] = self.user_cron

    def col_crontab(self):
        with open("/etc/crontab") as f:
            for line in f:
                if not ("=" in line or line.startswith(("#", " #")) or line == "\n"):
                    self.crontab.append(line)
        self.all_cron["crontab"] = self.crontab

    def tail_n(self, files, interval=10, num=10):
        pos = 0
        while True:
            with open(args) as f:
                cur_pos = f.seek(0,2)
                pos = cur_pos - interval
                interval += interval
                f.seek(pos)
                rest = f.readlines()
                if len(rest) > num:
                    return rest[::-1][:num]

    def hearbeat(self):
        self.col_crontab()
        self.col_cron()
        data = {
            'host': gethostname,
            "ip": get_ip(),
            "version": __version__,
            "timestamp": datetime.now().timestamp(),
            "cron_fact": self.data,
        }
        try:
            self.so.send(encode(data))
        except Exception as e:
            logging.error("send heartbeat error: {}".format(e))
            self.connect()

    def send(self):
        self.connect()
        while not event.is_set():
            self.read_cron()
            self.read_crontab()
            data = encode_data(self.data)
            self.socket.send(data)
            event.wait(5)
  
    def start(self):
        t = Thread(target=self.send)
        try:
            t.start()
        except:
            self.event.set()

    def shutdown(self):
        self.event.set()

if __name__ == '__main__':
    cron = GetCron()
    try:
        cron.start()
    except KeyboardInterrupt:
        cron.shutdown()
