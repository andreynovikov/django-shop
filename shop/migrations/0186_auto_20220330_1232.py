# Generated by Django 2.2.27 on 2022-03-30 09:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0185_integration_output_stock'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='ali',
        ),
        migrations.RemoveField(
            model_name='product',
            name='avito',
        ),
        migrations.RemoveField(
            model_name='product',
            name='beru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='mdbs',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sber',
        ),
        migrations.RemoveField(
            model_name='product',
            name='tax2',
        ),
        migrations.RemoveField(
            model_name='product',
            name='tax3',
        ),
        migrations.RemoveField(
            model_name='product',
            name='taxi',
        ),
    ]
