# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-18 22:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        ('accounts', '0016_add_profile_fields_for_agency'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgencyUser',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('auth.user',),
        ),
    ]