# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-08 15:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20170908_1125'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttype',
            name='jasper_module',
            field=models.CharField(blank=True, max_length=255, verbose_name='Module ของไฟล์ jasper'),
        ),
    ]