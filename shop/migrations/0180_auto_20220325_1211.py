# Generated by Django 2.2.27 on 2022-03-25 09:11

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0179_auto_20220325_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='admin_user_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='поля покупателя'),
        ),
        migrations.AddField(
            model_name='integration',
            name='uses_boxes',
            field=models.BooleanField(default=False, verbose_name='использует коробки'),
        ),
    ]
