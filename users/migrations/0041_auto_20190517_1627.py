# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-05-17 16:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0040_auto_20190426_1040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='facebook_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=255),
        ),
    ]