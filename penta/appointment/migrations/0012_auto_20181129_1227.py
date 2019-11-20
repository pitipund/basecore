# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-11-29 12:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appointment', '0011_appointment_specific_type'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='appointmentusertimeslot',
            unique_together=set([('appointment', 'user', 'timeslot', 'timeslot_end')]),
        ),
    ]