# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-04 18:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('shop', '0049_auto_20170516_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='site',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='sites.Site', verbose_name='сайт'),
            preserve_default=False,
        ),
    ]
