# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-06 17:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0113_auto_20180220_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='miscellaneousorder',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='วันที่เริ่มต้นบันทึก'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='miscellaneousorder',
            name='edit_user',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก'),
        ),
        migrations.AddField(
            model_name='miscellaneousorder',
            name='edited',
            field=models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด'),
        ),
    ]
