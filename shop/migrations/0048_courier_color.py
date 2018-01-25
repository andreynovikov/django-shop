# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0047_remove_courier_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='courier',
            name='color',
            field=colorfield.fields.ColorField(default='#000000', max_length=10),
        ),
    ]
