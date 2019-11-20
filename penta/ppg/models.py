from django.db import models
from django.conf import settings
from his.penta.curator.models import CuratorSupport
from his.penta.curator.models import CuratorChannel

import datetime
# Create your models here.

SANOOK_SOURCE = 1
TRUEVISION_SOURCE = 2

DAY_OF_WEEK_CHOICES = (
    (1, 'Sunday'),
    (2, 'Monday'),
    (3, 'Tuesday'),
    (4, 'Wednesday'),
    (5, 'Thursday'),
    (6, 'Friday'),
    (7, 'Saturday')
)

MATCH_WITH_CHOICES = (
    (1, 'EPG Name'),
    (2, 'EPG Channel Id'),
)

SOURCE_CHOICES = (
    (SANOOK_SOURCE, 'Sanook'),
    (TRUEVISION_SOURCE, 'True Vision'),
)


class Program(models.Model):
    id = models.AutoField(primary_key=True)
    curatorSupport = models.ForeignKey(CuratorSupport, verbose_name='Live Channel')
    name = models.CharField(max_length=200, verbose_name='Program Name')
    detail = models.TextField(max_length=2000, blank=True, null=True)
    icon = models.ImageField(upload_to=settings.SUPPORT_IM_PATH, verbose_name="Icon", blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    new_program = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Schedule(models.Model):
    id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program)
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES,default=1)
    start_time = models.TimeField()
    duration = models.IntegerField(help_text='minute')


class Episode(models.Model):
    id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program)
    name = models.CharField(max_length=200)
    detail = models.TextField(max_length=2000, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField()
    duration = models.IntegerField(help_text='minute')
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class CuratorSupportMapper(models.Model):
    id = models.AutoField(primary_key=True)
    curatorSupport = models.ForeignKey(CuratorSupport, verbose_name='Live Channel',blank=True,null=True)
    epg_name = models.CharField(max_length=200, verbose_name='EPG Name')
    epg_channel_id = models.CharField(max_length=200, verbose_name='EPG ChannelId')
    match_with = models.IntegerField(choices=MATCH_WITH_CHOICES,default=1)


class EPGSource(models.Model):
    id = models.AutoField(primary_key=True)
    curatorSupport = models.ForeignKey(CuratorSupport, verbose_name='Live Channel',blank=True,null=True)
    source = models.IntegerField(choices=SOURCE_CHOICES,default=SANOOK_SOURCE)
    url = models.CharField(max_length=500)
    enabled = models.BooleanField(default=True)

    def source_name(self):
        return SOURCE_CHOICES[self.source-1][1]


class LiveSuggestLog(models.Model):
    id = models.AutoField(primary_key=True)
    cpu_id = models.CharField(max_length=50)
    episode = models.ForeignKey(Episode)
    index = models.IntegerField()
    suggest_datetime = models.DateTimeField()


class CuratorChannelSuggestLog(models.Model):
    id = models.AutoField(primary_key=True)
    cpu_id = models.CharField(max_length=50)
    curatorChannel = models.ForeignKey(CuratorChannel)
    index = models.IntegerField()
    suggest_datetime = models.DateTimeField()
