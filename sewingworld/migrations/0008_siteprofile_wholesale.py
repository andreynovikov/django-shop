# Generated by Django 3.2.12 on 2023-02-17 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sewingworld', '0007_alter_siteprofile_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteprofile',
            name='wholesale',
            field=models.BooleanField(default=False, verbose_name='оптовый'),
        ),
    ]
