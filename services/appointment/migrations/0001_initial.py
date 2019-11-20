# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-05 15:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from his.penta.showtime import utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('address1', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('address2', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('province', models.CharField(blank=True, default='', max_length=30, null=True)),
                ('city', models.CharField(blank=True, default='', max_length=30, null=True)),
                ('district', models.CharField(blank=True, default='', max_length=30, null=True)),
                ('zipcode', models.CharField(blank=True, default='', max_length=10, null=True)),
                ('map_image', models.ImageField(blank=True, null=True, upload_to=utils.UploadToDir('uploaded/premise_content'), verbose_name='Map image')),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('place', models.TextField(blank=True, default='', null=True)),
                ('remark', models.TextField(blank=True, default='', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_finalize', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='AppointmentType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='AppointmentUserTimeslot',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('timeslot', models.IntegerField(db_index=True, default=0)),
                ('status', models.CharField(blank=True, default='', max_length=20, null=True)),
                ('is_owner', models.BooleanField(default=False)),
                ('is_answer', models.BooleanField(default=False)),
                ('is_ok', models.BooleanField(db_index=True, default=False)),
                ('is_finalize', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(blank=True, default='', max_length=30, null=True)),
                ('last_name', models.CharField(blank=True, default='', max_length=30, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('tel', models.CharField(blank=True, default='', max_length=13, null=True)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompositeChannel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='ExtraServiceDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to=utils.UploadToDir('uploaded/service_appointment'), verbose_name='Service appointment img.')),
                ('text', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('is_text_only', models.BooleanField(default=False)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Premise',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('is_official', models.BooleanField(default=True)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PremiseImage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to=utils.UploadToDir('uploaded/premise_content'), verbose_name='Premise image')),
                ('image_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ProviderAvailableSlot',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('start_slot', models.IntegerField(db_index=True, default=0)),
                ('end_slot', models.IntegerField(db_index=True, default=0)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointment.Provider')),
            ],
        ),
        migrations.CreateModel(
            name='ProviderType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('na', 'na'), ('caddy', 'caddy'), ('technician', 'technician'), ('golf_course', 'golf_course'), ('customer_house', 'customer_house')], default='na', max_length=32)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceAppointment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('is_parent', models.BooleanField(default=False)),
                ('remark', models.TextField(blank=True, default='', null=True)),
                ('is_provider_accept', models.BooleanField(default=False)),
                ('is_provider_ack', models.BooleanField(default=False)),
                ('is_done', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appointment.Appointment')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointment.Client')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointment.Provider')),
            ],
        ),
        migrations.CreateModel(
            name='UserAirTech',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('ex_profile', models.TextField(blank=True, default='', null=True)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserAvailableSlot',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('start_slot', models.IntegerField(db_index=True, default=0)),
                ('end_slot', models.IntegerField(db_index=True, default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserCaddy',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('ex_profile', models.TextField(blank=True, default='', null=True)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserCaddyPremise',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('caddy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointment.UserCaddy')),
                ('premise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointment.Premise')),
            ],
        ),
        migrations.CreateModel(
            name='UserDoctor',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserGolf',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserGolfCourt',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]