# Generated by Django 2.2.27 on 2022-03-25 10:00

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0180_auto_20220325_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='settings',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='настройки'),
        ),
    ]