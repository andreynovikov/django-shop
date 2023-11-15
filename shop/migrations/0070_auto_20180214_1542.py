# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-14 12:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0069_auto_20180214_1539'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='dispatch_date',
            new_name='delivery_handing_date',
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_dispatch_date',
            field=models.DateField(blank=True, null=True, verbose_name='дата получения'),
        ),
    ]