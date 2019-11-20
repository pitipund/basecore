from django.db import models

# Create your models here.
from django.db import models
from his.penta.curator.models import CuratorSupport


class TimingCount(models.Model):
    id = models.AutoField(primary_key=True)  # record id
    channel_support = models.ForeignKey(CuratorSupport, blank=False, null=False)  # Channel_3_id
    start_at = models.DateTimeField(auto_now=True, blank=True, null=True)  # e.g. 2014-July-1
    date = models.DateTimeField(auto_now=True, blank=True, null=True)  # e.g. 2014-July-1
    hour = models.IntegerField(default=0)  # 0-23
    timing = models.IntegerField(default=0)  # split for 0, 15, 30, 45
    count = models.IntegerField(default=0)  # as number

    class Meta:
        unique_together = (("channel_support", "date", "hour", "timing"),)


class CpuLastLog(models.Model):
    id = models.AutoField(primary_key=True)  # record id
    cpu_id = models.CharField(unique=True, max_length=255, db_index=True, null=False)
    latest_log = models.DateTimeField(blank=True, null=True)
    channel = models.ForeignKey(CuratorSupport, blank=False, null=False)
