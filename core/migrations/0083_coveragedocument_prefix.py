# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-01 17:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0082_auto_20171201_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='coveragedocument',
            name='prefix',
            field=models.CharField(default='R', max_length=8),
            preserve_default=False,
        ),
    ]