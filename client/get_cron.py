import os
import pytz
import glob
import json
import distro
import socket
import struct
import logging
import platform
from pyhocon import ConfigFactory
from datetime import datetime
from threading import Thread, Event

__version__ = "0.0.1"

BASE_DIR = os.getcwd()
conf = ConfigFactory.parse_file(os.path.join(BASE_DIR, "conf/client.conf"))

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

    def __init__(self, master, timezone='Asia/Shanghai'):
        self.master = master
        self.user_cron = []
        self.crontab = []
        self.cron_fact = {}
        self.files = glob.glob("/var/spool/cron/*")
        self.so = None
        self.timezone = timezone

    def connect(self):
        self.so = socket.socket()
        self.so.connect(self.master)
        print("4444")

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

    def get_timestamp(self):
        timez = pytz.timezone(self.timezone)
        now = timez.localize(datetime.now()).timestamp()
        return now

    def heartbeat(self):
        self.col_crontab()
        self.col_cron()
        data = {
            'hostname': platform.node(),
            "ip": get_ip(),
            "platform": platform.machine(),
            "sys_type": platform.system(),
            "dist": " ".join(distro.linux_distribution()),
            "version": __version__,
            "timestamp": self.get_timestamp(),
            "cron_info": self.cron_fact,
        }
        try:
            print(data)
            return encode_data(data)
        except Exception as e:
            logging.error("send heartbeat error: {}".format(e))
            self.connect()

    def send(self):
        self.connect()
        data = self.heartbeat()
        if data:
            self.so.send(data)
  
    def start(self):
        try:
            while not self.event.is_set():
                self.send()
                self.event.wait(30)
        except Exception as e:
            self.event.set()

    def shutdown(self):
        self.event.set()

if __name__ == '__main__':
    cron = GetCron((conf.get("server"), conf.get("port")))
    try:
        cron.start()
    except KeyboardInterrupt:
        cron.shutdown()
