# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0033_auto_20161125_1809'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='show_in_order',
            field=models.BooleanField(db_index=True, verbose_name='показывать в заказе', default=False),
        ),
    ]
