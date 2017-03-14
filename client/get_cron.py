import os
import pytz
import glob
import json
import psutil
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
    """
    获取本机的出口IP地址
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((dest_ip, 80))
        address, port = sock.getsockname()
        sock.close()
        return address
    except socket.error:
        return "127.0.0.1"


def encode_data(data):
    """
    对传输数据做封装，以length做为socket分隔
    """
    data = json.dumps(data).encode()
    length = len(data)
    return struct.pack("<l{}s".format(length), length, data)


class ColCronMixin:
    user_cron = []
    crontab = []
    cron_fact = {}

    def col_cron(self):
        """
        收集/var/logs/cron/中的crontab信息
        """
        files = glob.glob("/var/spool/cron/*")
        for files in files:
            with open(files) as f:
                for i in f:
                    self.user_cron.append(i.rstrip("\n"))
        if self.user_cron:
            self.cron_fact["user_cron"] = self.user_cron
            self.user_cron = []

    def col_crontab(self):
        """
        收集/etc/crontab中的crontab信息
        """
        with open("/etc/crontab") as f:
            for line in f:
                if not ("=" in line or line.startswith(("#", " #")) or line == "\n"):
                    self.crontab.append(line)
        if self.crontab:
            self.cron_fact["crontab"] = self.crontab
            self.crontab = []


class ColHardwareInfoMixin:
    CONVERT = {
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024
    }

    @staticmethod
    def col_cpu_counts():
        return psutil.cpu_count()

    @staticmethod
    def col_mem_counts():
        result = round(psutil.virtual_memory().total / CONVERT["GB"] + " GB")
        return result

    @staticmethod
    def col_net_counts():
        result = {}
        for k, v in psutil.net_if_addrs():
            v = v[0].address
            result[k] = v
        return result


class GetCron(ColCronMixin):
    event = Event()

    def __init__(self, master, timezone='Asia/Shanghai'):
        """
        收集client端的cron信息
        """
        self.master = master
        self.so = None
        self.timezone = timezone

    def connect(self):
        """
        与服务端建立连接
        """
        self.so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.so.connect(self.master)

    def get_timestamp(self):
        """
        获取当前的时间戳
        """
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

#    def tail_f(self, files, interval=10, num=10):
#        cur_pos = os.path.getsize(files)
#        while True:
#            with open(files) as f:
#                f.seek(0,2)
#                pos = cur_pos - interval
#                interval += interval
#                f.seek(pos)
#                rest = f.readlines()
#                if len(rest) > num:
#                    return rest[::-1][:num]


if __name__ == '__main__':
    cron = GetCron((conf.get("server"), conf.get("port")))
    try:
        cron.start()
    except KeyboardInterrupt:
        cron.shutdown()
