# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-11-26 15:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('appointment', '0007_auto_20181024_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='serviceappointment',
            name='business',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appointment.BusinessDetail'),
        ),
    ]