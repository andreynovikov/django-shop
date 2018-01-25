# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0042_auto_20170511_1955'),
    ]

    operations = [
        migrations.AddField(
            model_name='courier',
            name='color',
            field=colorfield.fields.ColorField(default='#000000', max_length=10),
        ),
        migrations.AddField(
            model_name='manager',
            name='color',
            field=colorfield.fields.ColorField(default='#000000', max_length=10),
        ),
    ]
