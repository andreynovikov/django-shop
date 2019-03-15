# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0043_auto_20170511_2006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='manafer',
        ),
        migrations.AddField(
            model_name='order',
            name='manager',
            field=models.ForeignKey(blank=True, verbose_name='менеджер', to='shop.Manager', null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(blank=True, verbose_name='курьер', to='shop.Courier', null=True, on_delete=models.SET_NULL),
        ),
    ]
