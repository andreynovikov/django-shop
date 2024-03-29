# Generated by Django 3.2.12 on 2023-12-25 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0213_product_comment_packer'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractor',
            name='bank_requisites',
            field=models.TextField(blank=True, verbose_name='банковские реквизиты'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='inn',
            field=models.CharField(blank=True, max_length=12, verbose_name='ИНН'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='is_seller',
            field=models.BooleanField(default=False, verbose_name='продавец'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='kpp',
            field=models.CharField(blank=True, max_length=9, verbose_name='КПП'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='legal_address',
            field=models.TextField(blank=True, verbose_name='юр. адрес'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='ogrn',
            field=models.CharField(blank=True, max_length=13, verbose_name='ОГРН'),
        ),
        migrations.AddField(
            model_name='contractor',
            name='postal_address',
            field=models.TextField(blank=True, verbose_name='физ. адрес'),
        ),
    ]
