# Generated by Django 3.2.12 on 2023-04-17 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0208_auto_20230417_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='svg_icon',
            field=models.TextField(blank=True, verbose_name='SVG иконка'),
        ),
    ]
