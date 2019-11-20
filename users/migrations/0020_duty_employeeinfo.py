# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-11-08 16:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0149_auto_20181011_1208'),
        ('users', '0019_auto_20180928_1457'),
    ]

    operations = [
        migrations.CreateModel(
            name='Duty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=250)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('head_staff', models.BooleanField(default=False, help_text='หัวหน้าแผนก')),
                ('incharge', models.BooleanField(default=False, help_text='สามารถเป็นหัวหน้าเวร')),
                ('duty', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_info', to='users.Duty')),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_info', to='users.Employee')),
                ('main_division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ef_main_divisions', to='core.Division')),
                ('sub_division', models.ManyToManyField(blank=True, related_name='ef_sub_divisions', to='core.Division')),
            ],
        ),
    ]