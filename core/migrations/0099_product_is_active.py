# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-12 15:59
from __future__ import unicode_literals

from django.db import migrations
import his.framework.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0098_encounteractionlog_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=his.framework.models.fields.EnumField(his.framework.models.fields._DummyEnum, default=1),
        ),
    ]