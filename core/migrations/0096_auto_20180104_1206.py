# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-04 12:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0095_package_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='package',
            options={'permissions': (('can_view_package', 'Can view Package'), ('can_action_package', 'Can create, update Package')), 'verbose_name': 'แพ็กเกจ'},
        ),
    ]
