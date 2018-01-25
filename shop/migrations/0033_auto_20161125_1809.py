# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0032_auto_20161125_1808'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=set([('product', 'supplier')]),
        ),
    ]
