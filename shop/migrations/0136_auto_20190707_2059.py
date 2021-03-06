# Generated by Django 2.1.7 on 2019-07-07 17:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0135_auto_20190618_2222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='country',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='shop.Country', verbose_name='Страна производства'),
        ),
        migrations.AlterField(
            model_name='product',
            name='developer_country',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='developed_product', to='shop.Country', verbose_name='Страна разработки'),
        ),
        migrations.AlterField(
            model_name='product',
            name='height',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='высота, см'),
        ),
        migrations.AlterField(
            model_name='product',
            name='km_class',
            field=models.CharField(blank=True, max_length=255, verbose_name='Класс машины'),
        ),
        migrations.AlterField(
            model_name='product',
            name='length',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='длина, см'),
        ),
        migrations.AlterField(
            model_name='product',
            name='ov_freearm',
            field=models.CharField(blank=True, max_length=255, verbose_name='Рукавная платформа'),
        ),
        migrations.AlterField(
            model_name='product',
            name='prom_weight',
            field=models.CharField(blank=True, max_length=255, verbose_name='Вес с упаковкой'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_autocutter',
            field=models.CharField(blank=True, max_length=255, verbose_name='Автоматическая обрезка нитей'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_diffeed',
            field=models.CharField(blank=True, max_length=255, verbose_name='Дифференциальный транспортер ткани'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_easythreading',
            field=models.CharField(blank=True, max_length=255, verbose_name='Облегчённая заправка петлителей'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_footheight',
            field=models.CharField(blank=True, max_length=50, verbose_name='Высота подъема лапки (нормальная/максимальная)'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_freearm',
            field=models.CharField(blank=True, max_length=50, verbose_name='Размеры рукавной платформы (длина/обхват), см'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_maxi',
            field=models.CharField(blank=True, max_length=255, verbose_name='Макси-узоры'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_needles',
            field=models.CharField(blank=True, max_length=255, verbose_name='Стандарт игл'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_power',
            field=models.FloatField(default=0, verbose_name='Потребляемая мощность, Вт'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sm_speedcontrol',
            field=models.CharField(blank=True, max_length=50, verbose_name='Регулятор (ограничитель) максимальной скорости'),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight',
            field=models.FloatField(default=0, verbose_name='Вес без упаковки, кг'),
        ),
        migrations.AlterField(
            model_name='product',
            name='width',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='ширина, см'),
        ),
    ]
