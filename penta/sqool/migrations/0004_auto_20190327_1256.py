# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-03-27 12:56
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sqool', '0003_auto_20190322_1641'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='content_payload',
            field=jsonfield.fields.JSONField(default={}),
        ),
        migrations.AlterField(
            model_name='message',
            name='content_type',
            field=models.CharField(choices=[('text', 'text'), ('image', 'image'), ('video', 'video'), ('file', 'file'), ('swap', 'swap')], max_length=10),
        ),
    ]
