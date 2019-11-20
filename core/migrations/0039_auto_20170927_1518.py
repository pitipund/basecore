# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-27 15:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_merge_20170926_1426'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='unit',
        ),
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.ForeignKey(help_text='หน่วยขาย', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Unit'),
        ),
    ]