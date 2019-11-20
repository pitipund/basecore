# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-12-20 11:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_merge_20181120_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_employee', to='users.Employee'),
        ),
    ]