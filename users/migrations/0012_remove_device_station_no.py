# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-04 11:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20171115_1642'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='station_no',
        ),
    ]