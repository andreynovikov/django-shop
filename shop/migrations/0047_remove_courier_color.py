# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0046_auto_20170515_1428'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courier',
            name='color',
        ),
    ]
