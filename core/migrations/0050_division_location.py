# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-11 18:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_miscellaneousorder_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='division',
            name='location',
            field=models.TextField(blank=True, verbose_name='ชื่อสถานที่'),
        ),
    ]