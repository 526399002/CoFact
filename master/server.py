import os
import django
import json
import struct
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cofact.settings")
django.setup()

from cron.models import *
from socketserver import BaseRequestHandler, ThreadingTCPServer


def _decode_data(data):
    return json.loads(data.decode())


class CollectionServer(BaseRequestHandler):
    buffer = None
   
    def ins_system_info(self, agent_id):
        System_info.objects.get_or_create(system=agent_id,
                                          platform=self.buffer["platform"],
                                          sys_type=self.buffer["sys_type"],
                                          distribution=self.buffer["dist"])

    def _get_crontab_file(self):
        return ", ".join(self.buffer["cron_info"]["crontab"])
 
    def _get_user_cron(self):
        return ", ".join(self.buffer["cron_info"]["user_cron"])

    def ins_crontab_info(self, agent_id):
        time_data = datetime.datetime.fromtimestamp(self.buffer["timestamp"])
        print(time_data)
        Crontab_info.objects.create(cron=agent_id,
                                    timestamp=time_data,
                                    version=self.buffer["version"],
                                    user_cron=self._get_user_cron(),
                                    crontab_file=self._get_crontab_file())

    def ins_agent(self):
        agent_id, *_ = Agent.objects.get_or_create(ip=self.buffer["ip"],
                                                   hostname=self.buffer["hostname"])
        self.ins_system_info(agent_id)
        self.ins_crontab_info(agent_id)
        self.buffer = None
    
    def handle(self):
        while True:
            buf = self.request.recv(4)
            length, *_ = struct.unpack("<l", buf)
            mid_data = self.request.recv(length)
            data, *_ = struct.unpack("<{}s".format(length), mid_data)
            self.buffer = _decode_data(data)
            print(self.buffer)
            self.ins_agent()
            if not data:
                break

if __name__ == '__main__':
    serv = ThreadingTCPServer(("", 15888), CollectionServer)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        serv.server_close()

