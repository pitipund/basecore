# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-01-16 16:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_auto_20190111_1725'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userfcmtoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_fcm_tokens', to=settings.AUTH_USER_MODEL),
        ),
    ]
