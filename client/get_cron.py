import os
import glob
import json
import socket
import struct
import logging
from datetime import datetime
from threading import Thread, Event

__version__ = "0.0.1"


def get_ip(dest_ip='115.239.211.112'):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((dest_ip, 80))
        address, port = sock.getsockname()
        sock.close()
        return address
    except socket.error:
        return "127.0.0.1"


def encode_data(data):
    data = json.dumps(data).encode()
    length = len(data)
    return struct.pack("<l{}s".format(length), length, data)


class GetCron:
    event = Event()

    def __init__(self, master):
        self.master = master
        self.user_cron = []
        self.crontab = []
        self.cron_fact = {}
        self.files = glob.glob("/var/spool/cron/*")
        self.so = None

    def connect(self):
        self.so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.so.connect(self.master)

    def col_cron(self): 
        for files in self.files:
            with open(files) as f:
                for i in f:
                    self.user_cron.append(i.rstrip("\n"))
        if self.user_cron:
            self.cron_fact["user_cron"] = self.user_cron
            self.user_cron = []

    def col_crontab(self):
        with open("/etc/crontab") as f:
            for line in f:
                if not ("=" in line or line.startswith(("#", " #")) or line == "\n"):
                    self.crontab.append(line)
        if self.crontab:
            self.cron_fact["crontab"] = self.crontab
            self.crontab = []

    def tail_f(self, files, interval=10, num=10):
        cur_pos = os.path.getsize(files)
        while True:
            with open(files) as f:
                f.seek(0,2)
                pos = cur_pos - interval
                interval += interval
                f.seek(pos)
                rest = f.readlines()
                if len(rest) > num:
                    return rest[::-1][:num]

    def heartbeat(self):
        self.col_crontab()
        self.col_cron()
        print("prepare data", socket.gethostname())
        data = {
            'host': socket.gethostname(),
            "ip": get_ip(),
            "version": __version__,
            "timestamp": datetime.now().timestamp(),
            "cron_fact": self.cron_fact,
        }
        try:
            print(data)
            return encode_data(data)
        except Exception as e:
            logging.error("send heartbeat error: {}".format(e))
            self.connect()

    def send(self):
        while not self.event.is_set():
            self.connect()
            data = self.heartbeat()
            self.so.send(data)
            self.event.wait(5)
  
    def start(self):
        t = Thread(target=self.send)
        try:
            t.start()
        except Exception as e:
            self.event.set()

    def shutdown(self):
        self.event.set()

if __name__ == '__main__':
    cron = GetCron(('172.16.20.119', 5888))
    try:
        cron.start()
    except KeyboardInterrupt:
        cron.shutdown()
