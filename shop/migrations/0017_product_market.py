# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_auto_20160728_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='market',
            field=models.BooleanField(default=False, verbose_name='Какая то хнень'),
        ),
    ]
