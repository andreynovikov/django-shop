# Generated by Django 2.1.7 on 2019-04-02 09:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0124_stock_reason'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advert',
            options={'ordering': ['order'], 'verbose_name': 'реклама', 'verbose_name_plural': 'рекламы'},
        ),
        migrations.AlterModelOptions(
            name='salesaction',
            options={'ordering': ['order'], 'verbose_name': 'акция', 'verbose_name_plural': 'акции'},
        ),
        migrations.AlterModelOptions(
            name='supplier',
            options={'ordering': ['order'], 'verbose_name': 'поставщик', 'verbose_name_plural': 'поставщики'},
        ),
        migrations.AddField(
            model_name='store',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.Supplier', verbose_name='склад'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='code1c',
            field=models.CharField(default='', max_length=50, verbose_name='код 1С'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sites.Site', verbose_name='сайт'),
        ),
    ]
