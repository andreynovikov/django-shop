# Generated by Django 3.2.12 on 2022-11-17 09:18

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sewingworld', '0003_auto_20220330_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteprofile',
            name='aliases',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None, verbose_name='домены-ссылки'),
        ),
        migrations.AlterField(
            model_name='siteprofile',
            name='manager_emails',
            field=models.CharField(blank=True, help_text='Можно несколько через запятую', max_length=255, verbose_name='адреса менеджеров'),
        ),
    ]