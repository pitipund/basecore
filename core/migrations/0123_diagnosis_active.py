# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-17 15:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0122_merge_20180410_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosis',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]