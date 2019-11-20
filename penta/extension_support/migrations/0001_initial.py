# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-05 15:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExtensionSupport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, default='', max_length=400, null=True)),
                ('url', models.URLField()),
                ('icon', models.ImageField(upload_to='uploaded/extension_support', verbose_name='Icon')),
                ('enabled', models.BooleanField(default=True)),
                ('sortkey', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Extension support',
            },
        ),
    ]
