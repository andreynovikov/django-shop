# Generated by Django 3.2.12 on 2024-02-29 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0215_integration_seller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integration',
            name='utm_source',
            field=models.CharField(db_index=True, max_length=20, unique=True, verbose_name='источник'),
        ),
    ]
