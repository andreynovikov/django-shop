# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-11 20:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0057_auto_20170726_0042'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='brief',
            field=models.TextField(blank=True, verbose_name='описание'),
        ),
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(blank=True, verbose_name='статья'),
        ),
    ]
