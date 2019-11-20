# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-20 11:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_encounter_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormPrintingCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('form_name', models.CharField(max_length=255, verbose_name='ชื่อไฟล์ jasper')),
                ('key', models.CharField(help_text='สิ่งที่ใช้ระบุเอกสารนั้นๆ เช่น pk, วันที่', max_length=255)),
                ('count', models.PositiveIntegerField(default=0, verbose_name='จำนวนครั้งที่พิมพ์')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='formprintingcount',
            unique_together=set([('form_name', 'key')]),
        ),
    ]
