# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-04 10:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0094_package'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
