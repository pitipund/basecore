# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-17 11:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0071_coverage_staging_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='encountercoverage',
            name='priority',
            field=models.IntegerField(default=99, verbose_name='ลำดับการเลือกใช้สิทธิ์'),
        ),
    ]
