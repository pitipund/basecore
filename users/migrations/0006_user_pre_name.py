# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-04 16:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_specialequip'),
        ('users', '0005_merge_20171004_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pre_name',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Prename', verbose_name='คำนำหน้าชื่อ'),
        ),
    ]
