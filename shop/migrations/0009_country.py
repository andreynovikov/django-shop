# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_auto_20160520_2243'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
                ('ename', models.CharField(max_length=100, verbose_name='англ. название')),
                ('enabled', models.BooleanField(default=True, verbose_name='включена')),
            ],
            options={
                'verbose_name': 'страна',
                'verbose_name_plural': 'страны',
            },
        ),
    ]
