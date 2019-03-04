# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0038_contractor'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='buyer',
            field=models.ForeignKey(related_name='покупатель', null=True, to='shop.Contractor', blank=True, verbose_name='покупатель 1С', on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='order',
            name='seller',
            field=models.ForeignKey(related_name='продавец', null=True, to='shop.Contractor', blank=True, verbose_name='продавец 1С', on_delete=models.SET_NULL),
        ),
    ]
