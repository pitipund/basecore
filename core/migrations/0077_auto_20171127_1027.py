# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-27 10:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_auto_20171123_1146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='miscellaneousorder',
            name='product',
            field=models.ForeignKey(help_text='a product to be charged', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Product'),
        ),
    ]
