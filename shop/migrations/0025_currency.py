# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0024_auto_20160906_2354'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('code', models.PositiveSmallIntegerField(primary_key=True, verbose_name='код', serialize=False)),
                ('name', models.CharField(max_length=20, verbose_name='название')),
                ('rate', models.DecimalField(verbose_name='курс', default=1, max_digits=5, decimal_places=2)),
            ],
            options={
                'verbose_name_plural': 'валюты',
                'verbose_name': 'валюта',
            },
        ),
    ]
