# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-07 13:49
from __future__ import unicode_literals

import datetime
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import his.users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('license_no', models.CharField(blank=True, max_length=100, verbose_name='เลขที่ใบประกอบวิชาชีพ')),
                ('employee_no', models.CharField(blank=True, max_length=50, verbose_name='รหัสบุคคล')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('active_users', his.users.models.ActiveUserManager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('computer_name', models.CharField(max_length=20, unique=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='ผู้ใช้ต้องล็อกอินจากเครื่องที่มี Computer Name และ IP Address ที่กำหนด(สามารถว่างไว้เพื่อตรวจสอบเฉพาะ Computer Name ได้)', null=True)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Division')),
            ],
        ),
        migrations.CreateModel(
            name='DevicePrinterMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='printers', to='users.Device')),
            ],
        ),
        migrations.CreateModel(
            name='HISPermission',
            fields=[
                ('permission_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.Permission')),
                ('type', models.IntegerField(choices=[(1, 'MANAGEMENT'), (2, 'SCREEN'), (3, 'RESOURCE'), (4, 'ACTION')], default=2)),
                ('identifier', models.CharField(help_text='Screen URL, Resource URL Name เช่น  fully_qualified_url, Action Name', max_length=100)),
                ('operation', models.IntegerField(choices=[(0, 'NONE'), (1, 'RETRIEVE'), (2, 'CREATE'), (3, 'UPDATE'), (4, 'DELETE')], default=0, help_text='ใช้กับ Permission ประเภท Resource เท่านั้น')),
            ],
            options={
                'ordering': ('type', 'identifier', 'operation'),
                'verbose_name': 'Permission',
                'verbose_name_plural': 'Permissions',
            },
            bases=('auth.permission',),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Location')),
            ],
        ),
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')),
                ('password', models.CharField(help_text='Old encrypted password', max_length=128)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='ชื่อตำแหน่งงาน')),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Human readable name for administrator', max_length=200)),
                ('jasper_paths', models.CharField(help_text='e.g. REG\\rptRegisterForm or list of comma separated path', max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('type', models.IntegerField(choices=[(1, 'GENERAL'), (2, 'DOCTOR'), (3, 'PHARMACIST'), (4, 'REGISTERED_NURSE')], default=1)),
                ('start_date', models.DateField(default=datetime.date.today, verbose_name='วันที่เริ่มต้นใช้ Role')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='วันที่สิ้นสุดการใช้ Role')),
                ('locations', models.ManyToManyField(blank=True, help_text='ผู้ใช้ต้องล็อกอินจากสถานที่ใน List ของสถานที่ที่กำหนดจึงจะมีสิทธิ์', to='users.Location')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Role')),
                ('permissions', models.ManyToManyField(blank=True, to='users.HISPermission')),
            ],
        ),
        migrations.CreateModel(
            name='Screen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='red', max_length=20)),
                ('url', models.CharField(max_length=200, unique=True)),
                ('display_seq', models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')),
                ('top_level', models.BooleanField(default=True, help_text='Display this screen in main menu')),
            ],
            options={
                'ordering': ('display_seq', 'id'),
            },
        ),
        migrations.AddField(
            model_name='deviceprintermap',
            name='printer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Printer'),
        ),
        migrations.AddField(
            model_name='deviceprintermap',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.ReportType'),
        ),
        migrations.AddField(
            model_name='device',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Location'),
        ),
        migrations.AddField(
            model_name='user',
            name='position',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Position'),
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(blank=True, to='users.Role'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='deviceprintermap',
            unique_together=set([('device', 'report')]),
        ),
    ]
