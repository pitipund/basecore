# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-03 11:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_pre_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]