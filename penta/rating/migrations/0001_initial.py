# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-05 15:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('curator', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CpuLastLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('cpu_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('latest_log', models.DateTimeField(blank=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='curator.CuratorSupport')),
            ],
        ),
        migrations.CreateModel(
            name='TimingCount',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('start_at', models.DateTimeField(auto_now=True, null=True)),
                ('date', models.DateTimeField(auto_now=True, null=True)),
                ('hour', models.IntegerField(default=0)),
                ('timing', models.IntegerField(default=0)),
                ('count', models.IntegerField(default=0)),
                ('channel_support', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='curator.CuratorSupport')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='timingcount',
            unique_together=set([('channel_support', 'date', 'hour', 'timing')]),
        ),
    ]
