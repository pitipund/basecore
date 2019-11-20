# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-05-31 15:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import his.framework.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0150_auto_20190530_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documenttype',
            name='type',
        ),
        migrations.AddField(
            model_name='documentcategory',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='documentcategory',
            name='display_seq',
            field=models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ'),
        ),
        migrations.AddField(
            model_name='documentcategory',
            name='parent',
            field=his.framework.models.fields.SelfReferenceForeignKey(blank=True, help_text='กรณีเป็นหมวดรอง field นี้คือหมวดที่เป็น parent', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.DocumentCategory'),
        ),
        migrations.AddField(
            model_name='scanneddocument',
            name='is_secret',
            field=models.BooleanField(default=False, verbose_name='เอกสารปกปิด'),
        ),
    ]