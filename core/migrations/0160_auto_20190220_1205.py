# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-02-20 12:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0159_merge_20190214_1810'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Action',
            new_name='UnitAction',
        ),
    ]