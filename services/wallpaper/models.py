# -*- coding: utf8 -*-
from __future__ import print_function, unicode_literals
import datetime

from django.core.files.storage import default_storage
from django.db.models.query_utils import Q
import os

from django.conf import settings
from django.db import models
from django.utils import timezone


class Wallpaper(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to=settings.WALLPAPER_PATH, verbose_name="Image")
    image_H3 = models.ImageField(blank=True, null=True, upload_to=settings.WALLPAPER_PATH, verbose_name="Image H3 Common")
    image_H3_inter = models.ImageField(blank=True, null=True, upload_to=settings.WALLPAPER_PATH, verbose_name="Image H3 Overseas")
    published = models.DateTimeField(blank=True, null=True, default=None,
                                     verbose_name=u'โชว์บนทีวีครั้งล่าสุด',
                                     help_text='The last time this wallpaper had been published. '
                                               'Set this field blank to show this wallpaper tomorrow.')
    start_publish_date = models.DateTimeField(blank=True, null=True, default=None,
                                              help_text=u'วันที่ให้เริ่มโชว์ภาพนี้ ควรกำหนดเวลาเป็น 0:00')
    end_publish_date = models.DateTimeField(blank=True, null=True, default=None,
                                            help_text=u'วันสุดท้ายที่ให้โชว์ภาพนี้ ควรกำหนดเวลาเป็น 0:00')
    isHighPriority = models.BooleanField(default=False, verbose_name='Promotion',
                                         help_text=u'Wallpaper ที่เป็น promotion จะถูกเลือกใช้ ก่อน Wallpaper อื่นๆ ในช่วงวันที่เดียวกัน')

    class Meta:
        app_label = 'wallpaper'
        ordering = ['published', ]
        get_latest_by = 'published'

    def __unicode__(self):
        return u'%s' % self.image

    def absolute_path(self):
        return '%s/%s' % (settings.MEDIA_ROOT, self.image)

    def h3_absolute_path(self):
        return '%s/%s' % (settings.MEDIA_ROOT, self.image_H3)

    def h3_inter_absolute_path(self):
        return '%s/%s' % (settings.MEDIA_ROOT, self.image_H3_inter)

    def image_preview(self):
        return u'<img src="%s" height=144 width="auto"/>' % self.image.url

    def image_H3_preview(self):
        return u'<img src="%s" height=144 width="auto"/>' % self.image_H3.url

    def image_H3_inter_preview(self):
        return u'<img src="%s" height=144 width="auto"/>' % self.image_H3_inter.url

    image_preview.short_description = 'Preview'
    image_preview.allow_tags = True
    image_H3_preview.short_description = 'Preview H3'
    image_H3_preview.allow_tags = True
    image_H3_inter_preview.short_description = 'Preview H3 Overseas'
    image_H3_inter_preview.allow_tags = True


def get_today_tuple():
    now = timezone.now()
    start = datetime.datetime.combine(now, datetime.time.min)
    end = datetime.datetime.combine(now, datetime.time.max)
    return (start, end)


def get_next_wallpaper(time=None):
    """
    Return latest wallpaper that is published

    Current wallpaper pickup algorithm
    1. [for promotion] today is between start publish date and end publish date and have isHighPriority = True
    2. [for seasonal wallpaper] today is between start publish date and end publish date
    3. [random] shuffled (use oldest published) pickup from
        3.1 no start publish date and no end publish date
        3.2 has start publish date before today and have no end publish date
        3.3 has end publish date after today and have no start publish date
    """
    if not time:
        time = timezone.now()

    # pickup isHighPriority
    wallpaper = Wallpaper.objects.filter(start_publish_date__lte=time,
                                         end_publish_date__gt=time,
                                         isHighPriority=True).first()
    if wallpaper:
        return wallpaper

    # pickup seasonal wallpaper
    wallpaper = Wallpaper.objects.filter(start_publish_date__lte=time,
                                         end_publish_date__gt=time).first()
    if wallpaper:
        return wallpaper

    # shuffle pickup
    wallpaper = Wallpaper.objects.filter(Q(start_publish_date__isnull=True) | Q(start_publish_date__lte=time))
    wallpaper = wallpaper.filter(Q(end_publish_date__isnull=True) | Q(end_publish_date__gt=time))
    wallpaper = wallpaper.first()
    if wallpaper:
        return wallpaper

    return None


def update_wallpaper(wallpaper=None):
    if wallpaper is None:
        wallpaper = get_next_wallpaper()
    if wallpaper:
        #
        target_path = os.path.join(settings.WALLPAPER_PATH, 'current.jpg')
        if default_storage.exists(target_path):
            default_storage.delete(target_path)
        try:
            path = default_storage.save(target_path, wallpaper.image)
            print(wallpaper, ' was copied to ', path)
        except Exception as e:
            pass

        target_path = os.path.join(settings.WALLPAPER_PATH, 'h3_current.jpg')
        if default_storage.exists(target_path):
            default_storage.delete(target_path)
        try:
            path = default_storage.save(target_path, wallpaper.image_H3)
            print(wallpaper, ' was copied to ', path)
        except Exception as e:
            path = default_storage.save(target_path, wallpaper.image)

        target_path = os.path.join(settings.WALLPAPER_PATH, 'h3_inter_current.jpg')
        if default_storage.exists(target_path):
            default_storage.delete(target_path)
        try:
            path = default_storage.save(target_path, wallpaper.image_H3_inter)
            print(wallpaper, ' was copied to ', path)
        except Exception as e:
            path = default_storage.save(target_path, wallpaper.image)

        wallpaper.published = timezone.now()
        wallpaper.save()
        
    return wallpaper.image
