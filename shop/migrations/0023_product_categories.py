# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0022_category_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='categories',
            field=mptt.fields.TreeManyToManyField(blank=True, null=True, to='shop.Category'),
        ),
    ]
