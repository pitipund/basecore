# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-02 13:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_runningnumber_updated'),
    ]

    operations = [
        migrations.RenameField(
            model_name='runningnumber',
            old_name='updated',
            new_name='reset_date',
        ),
    ]
