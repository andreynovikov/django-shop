# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0029_auto_20161119_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='order',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
