# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-24 21:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gsb', '0002_auto_20151025_2220'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ope',
            options={'get_latest_by': 'date', 'verbose_name': 'opération'},
        ),
    ]
