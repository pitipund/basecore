# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-18 15:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_encounternumberipd_encounternumberopd_encounternumbersss'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounter',
            name='note',
            field=models.CharField(blank=True, help_text='หมายเหตุ', max_length=255),
        ),
    ]
