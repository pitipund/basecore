# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-21 18:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0088_auto_20171214_1614'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankTransferSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('edited', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
                ('day_of_week', models.CharField(choices=[('0', 'จันทร์'), ('1', 'อังคาร'), ('2', 'พุธ'), ('3', 'พฤหัส'), ('4', 'ศุกร์'), ('5', 'เสาร์'), ('6', 'อาทิตย์')], default='0', max_length=1, verbose_name='วัน')),
                ('start_time', models.TimeField(help_text='เวลาเปิดทำการ', verbose_name='เวลาเปิดทำการ')),
                ('end_time', models.TimeField(help_text='เวลาปิดทำการ', verbose_name='เวลาปิดทำการ')),
                ('active', models.BooleanField(default=True, help_text='True = active, False = not active', verbose_name='active flag')),
                ('edit_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก')),
            ],
            options={
                'verbose_name': 'ตารางเวลาเปิดทำการของธนาคาร',
                'verbose_name_plural': 'ตารางเวลาเปิดทำการของธนาคาร',
            },
        ),
        migrations.CreateModel(
            name='BankTransferStopSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('edited', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
                ('date', models.DateTimeField(verbose_name='วันหยุดตามประเพณี')),
                ('active', models.BooleanField(default=True)),
                ('edit_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก')),
            ],
            options={
                'verbose_name': 'ตารางวันหยุดของธนาคาร',
                'verbose_name_plural': 'ตารางวันหยุดของธนาคาร',
            },
        ),
    ]
