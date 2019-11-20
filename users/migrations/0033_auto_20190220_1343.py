# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-02-20 13:43
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q

import his.framework.models.fields


def set_user_email(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    User = apps.get_model('users', 'User')
    Site = apps.get_model('sites', 'Site')
    site = 'localhost.local'
    all_sites = Site.objects.exclude(domain__in=['example.com', 'localhost', '127.0.0.1']).all()
    if all_sites:
        site = '.'.join(all_sites[0].domain.rsplit('.')[-2:])
    users = User.objects.filter(Q(email__isnull=True) | Q(email=''))
    for user in users:
        user.email = '{}@{}'.format(user.username, site)
        user.save()


def set_device_type(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    MobileDevice = apps.get_model('users', 'MobileDevice')
    devices = MobileDevice.objects.all()
    for device in devices:
        if device.device_type == 'etc':
            device.device_type = 0
        elif device.device_type == 'browser':
            device.device_type = 1
        elif device.device_type == 'android':
            device.device_type = 2
        elif device.device_type == 'ios':
            device.device_type = 3
        device.save()


def clear_device_type(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    MobileDevice = apps.get_model('users', 'MobileDevice')
    MobileDevice.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_auto_20190214_1739'), ('sites', '0002_alter_domain_unique')
    ]

    operations = [
        migrations.RunPython(set_user_email, migrations.RunPython.noop),
        migrations.RunPython(set_device_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mobiledevice',
            name='device_type',
            field=models.CharField(blank=True, db_index=False, max_length=10, null=True,
                                   choices=[('ios', 'ios'), ('android', 'android'),
                                            ('etc', 'etc'), ('browser', 'browser')])
        ),
        migrations.AlterField(
            model_name='mobiledevice',
            name='device_type',
            field=his.framework.models.fields.EnumField(his.framework.models.fields._DummyEnum, db_index=True, default=0),
        ),
        migrations.RunPython(migrations.RunPython.noop, clear_device_type),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, error_messages={'unique': 'This email have already been used.'}, max_length=254, null=True, unique=True, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='userotp',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='pre_name',
            field=models.ForeignKey(blank=True, help_text="user's pre name", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Prename'),
        ),
    ]
