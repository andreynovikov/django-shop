# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-09-26 09:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0109_auto_20180926_1032'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shopuser',
            name='is_admin',
        ),
    ]
