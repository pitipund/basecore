# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-19 15:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0013_auto_20171212_1423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='employee_no',
        ),
        migrations.RemoveField(
            model_name='user',
            name='license_no',
        ),
        migrations.RemoveField(
            model_name='user',
            name='position',
        ),
    ]