# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-12 11:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0052_category_basset_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractor',
            name='code',
            field=models.CharField(max_length=64, verbose_name='код 1С'),
        ),
    ]
