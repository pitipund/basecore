# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-01-23 16:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def migrate_content_id(apps, schema_editor):
    PentaAppointment = apps.get_model('appointment', 'Appointment')
    for penta_appointment in PentaAppointment.objects.all():
        if penta_appointment.content_type:
            penta_appointment.content_id = penta_appointment.id
            penta_appointment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('appointment', '0019_auto_20190118_1215'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='specific_type',
            new_name='content_type'
        ),
        migrations.AlterField(
            model_name='appointment',
            name='content_type',
            field=models.ForeignKey(editable=False, help_text='content type of business logic', null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='content_id',
            field=models.PositiveIntegerField(blank=True, editable=False, help_text='content id of business logic', null=True),
        ),
        migrations.RunPython(
            code=migrate_content_id,
            reverse_code=migrations.RunPython.noop
        ),
    ]
