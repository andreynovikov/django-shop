# Generated by Django 2.1.7 on 2021-03-06 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0159_auto_20210219_0013'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='taxi',
            field=models.BooleanField(db_index=True, default=False, verbose_name='выгружать в Яндекс.Такси'),
        ),
    ]
