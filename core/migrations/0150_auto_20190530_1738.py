# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-05-30 17:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def migrate_document_type(apps, schema_editor):
    """set document category to undefined"""
    DocumentCategory = apps.get_model('core', 'DocumentCategory')
    document_category, created = DocumentCategory.objects.get_or_create(
        code='UNDEFINED',
        defaults={
            'name': 'ไม่ระบุ'
        }
    )
    if created:
        print('create document category undefined.')

    DocumentType = apps.get_model('core', 'DocumentType')
    document_types = DocumentType.objects.all()
    if document_types.exists():
        for document_type in document_types:
            print('migrate [%s] %s set category to undefined.' % (document_type.id, document_type.name))
            document_type.category = document_category
            document_type.save()
    else:
        print('Document Type not found. skip migrate')

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0149_auto_20181011_1208'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Document Category',
                'verbose_name_plural': 'Document Category',
            },
        ),
        migrations.AddField(
            model_name='documenttype',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='core.DocumentCategory'),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_document_type, lambda: None),
    ]
