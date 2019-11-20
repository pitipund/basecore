# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-17 17:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0101_merge_20180116_1453'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackageOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('edited', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('perform_datetime', models.DateTimeField(help_text='a date and time when order was performed.')),
                ('active', models.BooleanField(default=True, help_text='is the order active?')),
                ('edit_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก')),
                ('encounter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='package_orders', to='core.Encounter')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Package')),
                ('patient_coverage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.PatientCoverage')),
                ('performing_division', models.ForeignKey(help_text='a division performed the order', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Division')),
                ('requesting_division', models.ForeignKey(help_text='a division requested the order', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Division')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
