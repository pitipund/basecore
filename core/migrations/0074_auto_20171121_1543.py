# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-21 15:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0073_auto_20171120_1245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisionworkschedule',
            name='end_time',
            field=models.TimeField(blank=True, help_text='เวลาที่สิ้นสุด', null=True, verbose_name='เวลาสิ้นสุด'),
        ),
    ]
