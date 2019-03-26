# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0039_auto_20170414_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='seller',
            field=models.ForeignKey(verbose_name='продавец 1С', blank=True, related_name='продавец', default=2, null=True, to='shop.Contractor', on_delete=models.SET_NULL),
        ),
    ]
