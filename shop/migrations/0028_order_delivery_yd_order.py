# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0027_auto_20161108_2329'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_yd_order',
            field=models.CharField(max_length=20, blank=True, verbose_name='ЯД заказ'),
        ),
    ]
