# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-03-26 11:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pentacenter', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='baseusersubscription',
            old_name='user',
            new_name='subscribed_user',
        ),
    ]