# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-28 16:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0079_merge_20171127_1408'),
    ]

    operations = [
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('edited', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='วันสิ้นสุด Episode')),
                ('edit_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Patient', verbose_name='ผู้ป่วยที่เกี่ยวข้อง')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='encounter',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Episode', verbose_name='Episode of care'),
        ),
    ]
