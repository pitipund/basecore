# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-02-21 18:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0161_auto_20190220_1254'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitStatusTransition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_unit_slot', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Unit Status Transition',
                'verbose_name': 'Unit Status Transition',
            },
        ),
        migrations.RemoveField(
            model_name='unitstatusallowedaction',
            name='allowed_actions',
        ),
        migrations.RemoveField(
            model_name='unitstatusallowedaction',
            name='unit_status',
        ),
        migrations.AddField(
            model_name='unitaction',
            name='action_class_name',
            field=models.CharField(blank=True, default='ACTION', help_text='action class name', max_length=255),
        ),
        migrations.AddField(
            model_name='unitaction',
            name='model_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='unitslot',
            name='owner_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='unitslot',
            name='owner_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='unitstatus',
            name='model_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='unitstatus',
            name='status_class_name',
            field=models.CharField(blank=True, default='STATUS', help_text='status class name', max_length=255),
        ),
        migrations.AlterField(
            model_name='unitaction',
            name='code',
            field=models.CharField(help_text='if import from LabelIntEnum this field = value', max_length=20),
        ),
        migrations.AlterField(
            model_name='unitaction',
            name='name',
            field=models.CharField(help_text='if import from LabelIntEnum this field = name', max_length=255),
        ),
        migrations.AlterField(
            model_name='unitslot',
            name='unit_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='unitstatus',
            name='code',
            field=models.CharField(help_text='if import from LabelIntEnum this field = value', max_length=20),
        ),
        migrations.AlterField(
            model_name='unitstatus',
            name='name',
            field=models.CharField(help_text='if import from LabelIntEnum this field = name', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='unitaction',
            unique_together=set([('model_type', 'action_class_name', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='unitstatus',
            unique_together=set([('model_type', 'status_class_name', 'code')]),
        ),
        migrations.DeleteModel(
            name='UnitStatusAllowedAction',
        ),
        migrations.AddField(
            model_name='unitstatustransition',
            name='from_unit_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.UnitStatus'),
        ),
        migrations.AddField(
            model_name='unitstatustransition',
            name='to_unit_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.UnitStatus'),
        ),
        migrations.AddField(
            model_name='unitstatustransition',
            name='unit_action',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.UnitAction'),
        ),
        migrations.AlterUniqueTogether(
            name='unitstatustransition',
            unique_together=set([('unit_action', 'from_unit_status')]),
        ),
    ]