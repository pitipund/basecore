# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-15 09:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_auto_20171109_1234'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='citizenwelfare',
            name='row_id',
        ),
        migrations.RemoveField(
            model_name='citizenwelfare',
            name='update_need',
        ),
        migrations.AlterField(
            model_name='citizenwelfare',
            name='citizen_no',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]