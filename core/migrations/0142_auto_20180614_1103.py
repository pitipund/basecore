# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-06-14 11:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0141_planitem_realize_every_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoveragePayerSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approval_code_required', models.BooleanField()),
            ],
        ),
        migrations.RemoveField(
            model_name='coverage',
            name='approval_code_required',
        ),
        migrations.AddField(
            model_name='coveragepayersettings',
            name='coverage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Coverage'),
        ),
        migrations.AddField(
            model_name='coveragepayersettings',
            name='payer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Payer'),
        ),
    ]
