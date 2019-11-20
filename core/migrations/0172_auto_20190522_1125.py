# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-05-22 11:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0171_department_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='url_en',
            field=models.CharField(blank=True, help_text='english url', max_length=250),
        ),
        migrations.AddField(
            model_name='department',
            name='url_zh',
            field=models.CharField(blank=True, help_text='chinese url', max_length=250),
        ),
        migrations.AlterField(
            model_name='department',
            name='url',
            field=models.CharField(blank=True, help_text='thai url', max_length=250),
        ),
    ]
