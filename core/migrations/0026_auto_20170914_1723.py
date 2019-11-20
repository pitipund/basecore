# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-14 17:23
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20170913_1235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planitem',
            name='dates',
            field=jsonfield.fields.JSONField(blank=True, default=list, help_text='วันที่/เดือน/ปี ที่จะทำ (พ.ศ.)', verbose_name='วันที่จะทำ (กำหนดได้หลายวัน)'),
        ),
        migrations.AlterField(
            model_name='planitem',
            name='times',
            field=jsonfield.fields.JSONField(blank=True, default=list, verbose_name='เวลาที่จะทำ (กำหนดได้หลายเวลา)'),
        ),
        migrations.AlterField(
            model_name='planitem',
            name='week_days',
            field=jsonfield.fields.JSONField(blank=True, default=list, verbose_name='วันในสัปดาห์'),
        ),
    ]