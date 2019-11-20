# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-09-27 16:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import his.framework.models.fields
from his.users.models import PrintServer, ReportType


def set_print_server_to_report_type(apps, schema_editor):
    print_server = PrintServer.objects.filter(url='http://192.168.56.150:9080/printserver/print',
                                              active=True).first()
    if not print_server:
        print_server = PrintServer()
        print_server.url = 'http://192.168.56.150:9080/printserver/print'
        print_server.save()

    for r in ReportType.objects.all():
        r.print_server = print_server
        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_auto_20180515_1131'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrintServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(help_text='Example: http://192.168.56.150:9080/printserver/print')),
                ('type', his.framework.models.fields.EnumField(his.framework.models.fields._DummyEnum, default=1)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Print Server',
            },
        ),
        migrations.RenameField(
            model_name='reporttype',
            old_name='jasper_paths',
            new_name='report_path',
        ),
        migrations.AlterField(
            model_name='deviceprintermap',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='map_report_type', to='users.ReportType'),
        ),
        migrations.AddField(
            model_name='reporttype',
            name='print_server',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.PrintServer'),
        ),
        migrations.RunPython(set_print_server_to_report_type),
    ]