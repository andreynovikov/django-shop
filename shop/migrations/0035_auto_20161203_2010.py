# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0034_supplier_show_in_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='number_inet',
        ),
        migrations.RemoveField(
            model_name='product',
            name='number_prol',
        ),
    ]
