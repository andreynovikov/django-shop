# Generated by Django 3.2.12 on 2022-05-17 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0187_auto_20220515_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='productreview',
            name='advantage',
            field=models.TextField(blank=True, max_length=3000, verbose_name='достоинства'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='disadvantage',
            field=models.TextField(blank=True, max_length=3000, verbose_name='недостатки'),
        ),
    ]
