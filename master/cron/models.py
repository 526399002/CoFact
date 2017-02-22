from django.db import models

# Create your models here.
class Agent(models.Model):
    ip = models.CharField(max_length=128, blank=True, null=True, default='', verbose_name='主机IP')
    hostname = models.CharField(max_length=32, blank=True, null=True, default='', verbose_name='主机名')


class System_info(models.Model):
    system = models.ForeignKey(Agent)
    platform = models.CharField(max_length=64, default="", verbose_name='系统平台')
    sys_type = models.CharField(max_length=16, default="", verbose_name='操作系统')
    distribution = models.CharField(max_length=128, default="", verbose_name='系统发行版')


class Crontab_info(models.Model):
    cron = models.ForeignKey(Agent)
    timestamp = models.DateTimeField()
    version = models.CharField(max_length=16, default='', verbose_name="客户端版本")
    user_cron = models.TextField(blank=True, null=True, default="", verbose_name='/etc/spool/cron 信息')
    crontab_file = models.TextField(blank=True, null=True, default='', verbose_name='/etc/crontab 信息')
