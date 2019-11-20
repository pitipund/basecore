# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-21 18:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0073_auto_20171120_1245'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductFilterGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=200)),
                ('products', models.ManyToManyField(to='core.Product')),
            ],
        ),
    ]
