# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-17 16:48
from __future__ import unicode_literals

from django.db import migrations, models
import his.framework.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0126_auto_20180504_1159'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttype',
            name='code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='documenttype',
            name='type',
            field=his.framework.models.fields.EnumField(his.framework.models.fields._DummyEnum, default=2),
        ),
    ]