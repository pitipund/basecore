# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-23 15:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0137_scanneddocument_cancel_note'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'verbose_name': 'Episode of care', 'verbose_name_plural': 'Episode of care'},
        ),
    ]