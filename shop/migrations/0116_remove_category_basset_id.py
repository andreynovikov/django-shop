# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-31 09:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0115_auto_20181029_1309'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='basset_id',
        ),
    ]
