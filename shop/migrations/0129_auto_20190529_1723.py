# Generated by Django 2.1.7 on 2019-05-29 14:23

from django.db import migrations
import shop.models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0128_auto_20190425_1317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopuser',
            name='username',
            field=shop.models.UsernameField(max_length=100, verbose_name='прозвище'),
        ),
    ]
