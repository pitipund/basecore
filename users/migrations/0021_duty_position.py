# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-11-08 16:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_duty_employeeinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='duty',
            name='position',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='users.Position'),
            preserve_default=False,
        ),
    ]