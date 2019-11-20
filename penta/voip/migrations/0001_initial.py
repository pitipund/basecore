# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-05 15:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserVOIPRegister',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(blank=True, default='', max_length=32)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='voip_register', to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'verbose_name_plural': 'User VOIP Registers',
                'verbose_name': 'User VOIP Register',
            },
        ),
        migrations.CreateModel(
            name='VOIPServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=15)),
                ('port', models.IntegerField()),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name_plural': 'VOIP Servers',
                'verbose_name': 'VOIP Server',
            },
        ),
    ]