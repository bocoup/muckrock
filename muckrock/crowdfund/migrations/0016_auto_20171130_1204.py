# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-30 12:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crowdfund', '0015_auto_20170114_1858'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecurringCrowdfundPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('amount', models.PositiveIntegerField()),
                ('show', models.BooleanField(default=False)),
                ('customer_id', models.CharField(max_length=255)),
                ('subscription_id', models.CharField(max_length=255, unique=True)),
                ('payment_failed', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('deactivated_datetime', models.DateTimeField(blank=True, null=True)),
                ('crowdfund', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recurring_payments', to='crowdfund.Crowdfund')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recurring_crowdfund_payments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='crowdfundpayment',
            name='recurring',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='crowdfund.RecurringCrowdfundPayment'),
        ),
    ]