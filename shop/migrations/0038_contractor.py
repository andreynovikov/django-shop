# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0037_auto_20170322_1902'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contractor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(max_length=20, verbose_name='код 1С')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
            ],
            options={
                'verbose_name_plural': 'контрагенты',
                'verbose_name': 'контрагент',
            },
        ),
    ]
