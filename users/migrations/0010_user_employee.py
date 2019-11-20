# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-15 09:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_device_zone'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Employee'),
        ),
    ]