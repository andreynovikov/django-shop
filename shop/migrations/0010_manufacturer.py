# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0009_country'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='код', max_length=30)),
                ('name', models.CharField(verbose_name='название', max_length=150)),
                ('machinemaker', models.BooleanField(default=False, verbose_name='машины делает')),
                ('accessorymaker', models.BooleanField(default=False, verbose_name='аксессуары делает')),
            ],
            options={
                'verbose_name_plural': 'производители',
                'verbose_name': 'производитель',
            },
        ),
    ]
