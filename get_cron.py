import re
import struct
import glob
import json
from socket import socket, AF_INET, SOCK_STREAM


def encode_data(data):
    data = json.dumps(data).encode()
    length = len(data)
    return struct.pack("<l{}s".format(length). length, data)

class GetCron:
    def __init__(self, master):
        self.master = master
        self.user_cron = []
        self.crontab = []
        self.data = {}
        self.files = glob.glob("/var/spool/cron/*")
        self.so = None

    def connect(self):
        self.so = socket(AF_INET, SOCK_STREAM)
        self.so.connect(self.master)

    def read_cron(self): 
        for files in self.files:
            with open(i) as f:
                for i in f:
                    self.user_cron.append(i.rstrip("\n")) 
        self.data["user_cron"] = self.user_cron

    def read_crontab(self):
        with open("/etc/crontab") as f:
            for line in f:
                if not ("=" in line or line.startswith(("#", " #")) or line == "\n"):
                    self.crontab.append(line)
        self.data["crontab"] = self.crontab
   
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

if __name__ == '__main__':
    get = GetCron()
    get.read_crontab()
    print(get.crontab)
