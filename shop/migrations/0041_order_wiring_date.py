# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0040_auto_20170417_1025'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='wiring_date',
            field=models.DateField(null=True, verbose_name='дата проводки', blank=True),
        ),
    ]
