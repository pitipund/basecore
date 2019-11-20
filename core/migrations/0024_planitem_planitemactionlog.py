# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-13 10:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import his.framework.models.fields
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0023_documenttype_jasper_module'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('edited', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
                ('status', his.framework.models.fields._StatableStatusField(default=0, editable=False)),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='วันที่เริ่มต้น')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='วันที่สิ้นสุด')),
                ('week_days', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='วันในสัปดาห์')),
                ('day_take', models.PositiveIntegerField(blank=True, null=True, verbose_name='จำนวนวันที่ทำ')),
                ('day_skip', models.PositiveIntegerField(blank=True, null=True, verbose_name='จำนวนวันที่ไม่ทำ')),
                ('occurrence', models.PositiveIntegerField(blank=True, null=True, verbose_name='จำนวนครั้งที่ทำ')),
                ('dates', jsonfield.fields.JSONField(blank=True, help_text='วันที่/เดือน/ปี ที่จะทำ (พ.ศ.)', null=True, verbose_name='วันที่จะทำ (กำหนดได้หลายวัน)')),
                ('times', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='เวลาที่จะทำ (กำหนดได้หลายเวลา)')),
                ('plan_summary', models.TextField(help_text='เมื่อมีการ บันทึก/แก้ไข DoctorOrder จะต้อง update plan_summary', verbose_name='สรุปข้อมูลของ DoctorOrder')),
                ('actual_orders', models.ManyToManyField(help_text='PlanItem ที่ DoctorOrder ใช้ตอนถูก                                            Clone ซึ่งจะต้องมีแค่ 1 เท่านั้น', related_name='created_from_plan_item', to='core.DoctorOrder', verbose_name='รายการที่ถูกสร้างแล้ว')),
                ('edit_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='ผู้บันทึก')),
                ('plan_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_items', to='core.DoctorOrder', verbose_name='รายการต้นแบบที่จะถูกสร้างเมื่อถึงเวลา')),
            ],
            options={
                'verbose_name': 'ตารางวางแผนการทำรายการแบบต่อเนื่อง',
            },
        ),
        migrations.CreateModel(
            name='PlanItemActionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', his.framework.models.fields.EnumField(his.framework.models.fields._DummyEnum)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('statable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='core.PlanItem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
