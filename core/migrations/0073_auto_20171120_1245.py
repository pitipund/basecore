# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-20 12:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0072_encountercoverage_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='encountercoverage',
            name='refer_no',
            field=models.CharField(blank=True, help_text='เลขรหัสหนังสือส่งตัว', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='patientcoverage',
            name='refer_no',
            field=models.CharField(blank=True, help_text='เลขรหัสหนังสือส่งตัว', max_length=255, null=True),
        ),
        migrations.RemoveField(
            model_name='encountercoverage',
            name='referer',
        ),
        migrations.RemoveField(
            model_name='patientcoverage',
            name='referer',
        ),
        migrations.AddField(
            model_name='encountercoverage',
            name='referer',
            field=models.ForeignKey(blank=True, help_text='โรงพยาบาลต้นสังกัดกรณีผู้ป่วย Refer-in', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Referer'),
        ),
        migrations.AddField(
            model_name='patientcoverage',
            name='referer',
            field=models.ForeignKey(blank=True, help_text='โรงพยาบาลต้นสังกัดกรณีผู้ป่วย Refer-in', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Referer'),
        ),
    ]
