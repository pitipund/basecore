# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-05-04 11:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0125_coverage_approval_code_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocklog',
            name='balance',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='stock',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='stocklog',
            name='stock',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='core.Stock'),
        ),
    ]