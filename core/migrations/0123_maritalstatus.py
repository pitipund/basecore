# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-04-17 12:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0122_merge_20180410_1921'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaritalStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='ชื่อของตัวเลือก')),
                ('display_seq', models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')),
                ('is_active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=4, unique=True)),
            ],
            options={
                'ordering': ['display_seq'],
                'managed': True,
            },
        ),
    ]