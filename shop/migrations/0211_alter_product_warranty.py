# Generated by Django 3.2.12 on 2023-07-26 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0210_auto_20230726_1321'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='warranty',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='гарантия, мес'),
        ),
    ]
