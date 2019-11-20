# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-08-08 16:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0152_merge_20190725_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctororder',
            name='doctor_edit_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='วันเวลาที่แพทย์แก้ไข'),
        ),
        migrations.AddField(
            model_name='doctororder',
            name='edited_doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Doctor', verbose_name='แพทย์ผู้แก้ไข'),
        ),
    ]
