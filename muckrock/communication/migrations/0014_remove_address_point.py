# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-23 14:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0013_auto_20180713_1340'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='point',
        ),
    ]
