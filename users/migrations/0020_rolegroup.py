# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-06-05 10:11
from __future__ import unicode_literals

from django.db import migrations, models


def set_can_view_secret_document(apps, schema_editor):
    RoleGroup = apps.get_model('users', 'RoleGroup')
    RoleGroup.objects.get_or_create(
        code='CAN_VIEW_SECRET_DOCUMENT_CODE',
        defaults={
            'name': 'สามารถดูเอกสารปกปิด'
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_auto_20180928_1457'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('roles', models.ManyToManyField(blank=True, to='users.Role')),
            ],
            options={
                'verbose_name': 'Role Group',
                'verbose_name_plural': 'Role Group',
            },
        ),
        migrations.RunPython(set_can_view_secret_document, lambda: None),
    ]