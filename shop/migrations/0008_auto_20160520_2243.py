# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_auto_20160212_2226'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='absent',
            field=models.BooleanField(default=False, verbose_name='Нет в продаже'),
        ),
        migrations.AddField(
            model_name='product',
            name='available',
            field=models.CharField(max_length=255, blank=True, verbose_name='Наличие'),
        ),
        migrations.AddField(
            model_name='product',
            name='bid',
            field=models.CharField(max_length=10, blank=True, verbose_name='Ставка маркета для основной выдачи'),
        ),
        migrations.AddField(
            model_name='product',
            name='cbid',
            field=models.CharField(max_length=10, blank=True, verbose_name='Ставка маркета для карточки модели'),
        ),
        migrations.AddField(
            model_name='product',
            name='complect',
            field=models.TextField(verbose_name='Комплектация', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='consultant_delivery_price',
            field=models.FloatField(default=0, verbose_name='Стоимость доставки с консультантом'),
        ),
        migrations.AddField(
            model_name='product',
            name='coupon',
            field=models.BooleanField(default=False, verbose_name='Предлагать купон'),
        ),
        migrations.AddField(
            model_name='product',
            name='dealertxt',
            field=models.TextField(verbose_name='Текст про официального дилера', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='delivery',
            field=models.SmallIntegerField(default=0, verbose_name='Доставка'),
        ),
        migrations.AddField(
            model_name='product',
            name='descr',
            field=models.TextField(verbose_name='Краткое описание', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='deshevle',
            field=models.BooleanField(default=False, verbose_name='Нашли дешевле'),
        ),
        migrations.AddField(
            model_name='product',
            name='dimensions',
            field=models.CharField(max_length=255, blank=True, verbose_name='Размеры'),
        ),
        migrations.AddField(
            model_name='product',
            name='enabled',
            field=models.BooleanField(default=False, verbose_name='включён'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_hard',
            field=models.CharField(max_length=50, blank=True, verbose_name='Тяжелые ткани'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_leather',
            field=models.CharField(max_length=50, blank=True, verbose_name='Кожа'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_lite',
            field=models.CharField(max_length=50, blank=True, verbose_name='Легкие ткани'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_medium',
            field=models.CharField(max_length=50, blank=True, verbose_name='Средние ткани'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_stretch',
            field=models.CharField(max_length=50, blank=True, verbose_name='Трикотаж'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_veryhard',
            field=models.CharField(max_length=50, blank=True, verbose_name='Очень тяжелые ткани'),
        ),
        migrations.AddField(
            model_name='product',
            name='fabric_verylite',
            field=models.CharField(max_length=50, blank=True, verbose_name='Очень легкие ткани'),
        ),
        migrations.AddField(
            model_name='product',
            name='firstpage',
            field=models.BooleanField(default=False, verbose_name='Показать на первой странице'),
        ),
        migrations.AddField(
            model_name='product',
            name='gift',
            field=models.BooleanField(default=False, verbose_name='Годится в подарок'),
        ),
        migrations.AddField(
            model_name='product',
            name='internetonly',
            field=models.BooleanField(default=False, verbose_name='Только в интернет-магазине'),
        ),
        migrations.AddField(
            model_name='product',
            name='isnew',
            field=models.BooleanField(default=False, verbose_name='Новинка'),
        ),
        migrations.AddField(
            model_name='product',
            name='km_class',
            field=models.CharField(max_length=255, blank=True, verbose_name='Класс вязальной машины'),
        ),
        migrations.AddField(
            model_name='product',
            name='km_font',
            field=models.CharField(max_length=255, blank=True, verbose_name='Количество фонтур'),
        ),
        migrations.AddField(
            model_name='product',
            name='km_needles',
            field=models.CharField(max_length=255, blank=True, verbose_name='Количество игл'),
        ),
        migrations.AddField(
            model_name='product',
            name='km_prog',
            field=models.CharField(max_length=255, blank=True, verbose_name='Способ программирования'),
        ),
        migrations.AddField(
            model_name='product',
            name='km_rapport',
            field=models.CharField(max_length=255, blank=True, verbose_name='Раппорт программируемого рисунка'),
        ),
        migrations.AddField(
            model_name='product',
            name='measure',
            field=models.CharField(max_length=10, blank=True, verbose_name='Единицы'),
        ),
        migrations.AddField(
            model_name='product',
            name='not_for_sale',
            field=models.BooleanField(default=False, verbose_name='Не показывать кнопку заказа'),
        ),
        migrations.AddField(
            model_name='product',
            name='num',
            field=models.SmallIntegerField(default=0, verbose_name='В наличии'),
        ),
        migrations.AddField(
            model_name='product',
            name='opinion',
            field=models.CharField(max_length=255, blank=True, verbose_name='Ссылка на обсуждение модели'),
        ),
        migrations.AddField(
            model_name='product',
            name='oprice',
            field=models.PositiveIntegerField(default=0, verbose_name='Цена розничная'),
        ),
        migrations.AddField(
            model_name='product',
            name='ov_freearm',
            field=models.CharField(max_length=255, blank=True, verbose_name='Cвободный рукав оверлока'),
        ),
        migrations.AddField(
            model_name='product',
            name='present',
            field=models.CharField(max_length=255, blank=True, verbose_name='Подарок к этому товару'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_autothread',
            field=models.CharField(max_length=255, blank=True, verbose_name='Автоматический нитеотводчик'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_bhlenght',
            field=models.CharField(max_length=255, blank=True, verbose_name='Длина петли'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_button_diainner',
            field=models.CharField(max_length=255, blank=True, verbose_name='Внутренний диаметр пуговицы'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_button_diaouter',
            field=models.CharField(max_length=255, blank=True, verbose_name='Наружный диаметр пуговицы'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_cutting',
            field=models.CharField(max_length=255, blank=True, verbose_name='Обрезка нити'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_fabric_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип материала'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_foot_lift',
            field=models.CharField(max_length=255, blank=True, verbose_name='Высота подъема лапки'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_needle_height',
            field=models.CharField(max_length=255, blank=True, verbose_name='Ход игловодителя'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_needle_num',
            field=models.CharField(max_length=255, blank=True, verbose_name='Количество игл'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_needle_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Размер и тип иглы'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_needle_width',
            field=models.CharField(max_length=255, blank=True, verbose_name='Расстояние между иглами'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_oil_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип смазки'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_overstitch_lenght',
            field=models.CharField(max_length=255, blank=True, verbose_name='Максимальная длина обметочного стежка'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_overstitch_width',
            field=models.CharField(max_length=255, blank=True, verbose_name='Максимальная ширина обметочного стежка'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_platform_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип платформы'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_power',
            field=models.CharField(max_length=255, blank=True, verbose_name='Мощность'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_shuttle_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип челнока'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_speed',
            field=models.CharField(max_length=255, blank=True, verbose_name='Максимальная скорость шитья'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_stitch_lenght',
            field=models.CharField(max_length=255, blank=True, verbose_name='Длина стежка'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_stitch_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип стежка'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_stitch_width',
            field=models.CharField(max_length=255, blank=True, verbose_name='Ширина зигзагообразной строчки'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_threads_num',
            field=models.CharField(max_length=255, blank=True, verbose_name='Количество нитей'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_transporter_type',
            field=models.CharField(max_length=255, blank=True, verbose_name='Тип транспортера'),
        ),
        migrations.AddField(
            model_name='product',
            name='prom_weight',
            field=models.CharField(max_length=255, blank=True, verbose_name='Вес брутто'),
        ),
        migrations.AddField(
            model_name='product',
            name='recomended',
            field=models.BooleanField(default=False, verbose_name='Рекомендуем'),
        ),
        migrations.AddField(
            model_name='product',
            name='runame',
            field=models.CharField(max_length=200, blank=True, verbose_name='Русское название'),
        ),
        migrations.AddField(
            model_name='product',
            name='sales_notes',
            field=models.CharField(max_length=50, blank=True, verbose_name='Yandex.Market Sales Notes'),
        ),
        migrations.AddField(
            model_name='product',
            name='shortdescr',
            field=models.TextField(verbose_name='Характеристика', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='show_on_sw',
            field=models.BooleanField(default=True, verbose_name='Показать на основной витрине'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_advisor',
            field=models.CharField(max_length=255, blank=True, verbose_name='Швейный советник'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_advisor_bool',
            field=models.BooleanField(default=False, verbose_name='Есть швейный советник'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_alphabet',
            field=models.CharField(max_length=255, blank=True, verbose_name='Алфавит'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_alphabet_bool',
            field=models.BooleanField(default=False, verbose_name='Есть алфавит'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_autobuttonhole_bool',
            field=models.BooleanField(default=False, verbose_name='Делает автоматически петлю'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_autocutter',
            field=models.CharField(max_length=255, blank=True, verbose_name='Автоматический нитеобрезатель'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_autostop',
            field=models.CharField(max_length=50, blank=True, verbose_name='Автостоп при намотке нитки на шпульку'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_buttonhole',
            field=models.CharField(max_length=255, blank=True, verbose_name='Режим вымётывания петли'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_constant',
            field=models.CharField(max_length=50, blank=True, verbose_name='Электронный стабилизатор усилия прокола'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_cover',
            field=models.CharField(max_length=50, blank=True, verbose_name='Чехол'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_diffeed',
            field=models.CharField(max_length=255, blank=True, verbose_name='Дифференциальный транспортер'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_display',
            field=models.TextField(verbose_name='Дисплей', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_dualtransporter',
            field=models.CharField(max_length=50, blank=True, verbose_name='Верхний транспортёр'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_dualtransporter_bool',
            field=models.BooleanField(default=False, verbose_name='Есть встроенный транспортер'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_easythreading',
            field=models.CharField(max_length=255, blank=True, verbose_name='Простая заправка петлителей'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_feedwidth',
            field=models.CharField(max_length=50, blank=True, verbose_name='Ширина гребёнки транспортера, мм'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_fix',
            field=models.CharField(max_length=255, blank=True, verbose_name='Закрепка'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_footheight',
            field=models.CharField(max_length=50, blank=True, verbose_name='Величина зазора под лапкой (нормальный/двойной)'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_freearm',
            field=models.CharField(max_length=50, blank=True, verbose_name='Размеры "свободного рукава" (длина/обхват), см'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_kneelift',
            field=models.CharField(max_length=255, blank=True, verbose_name='Коленный рычаг подъема лапки'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_light',
            field=models.CharField(max_length=50, blank=True, verbose_name='Тип освещения'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_maxi',
            field=models.CharField(max_length=255, blank=True, verbose_name='Макси узоры'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_maxi_bool',
            field=models.BooleanField(default=False, verbose_name='Есть макси-узоры'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_memory',
            field=models.CharField(max_length=255, blank=True, verbose_name='Память'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_mirror',
            field=models.CharField(max_length=255, blank=True, verbose_name='Зеркальное отображение образца строчки'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_needles',
            field=models.CharField(max_length=255, blank=True, verbose_name='Иглы'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_needleupdown',
            field=models.CharField(max_length=50, blank=True, verbose_name='Программируемая остановка иглы в верхнем/нижнем положении'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_organizer',
            field=models.CharField(max_length=50, blank=True, verbose_name='Органайзер'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_patterncreation_bool',
            field=models.BooleanField(default=False, verbose_name='Есть функция создания строчек'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_platformlenght',
            field=models.CharField(max_length=50, blank=True, verbose_name='Длина платформы, см'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_power',
            field=models.FloatField(default=0, verbose_name='Потребляемая мощность, вт'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_presscontrol',
            field=models.CharField(max_length=50, blank=True, verbose_name='Регулятор давления лапки'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_ruler',
            field=models.CharField(max_length=50, blank=True, verbose_name='Линейка на корпусе'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_shuttletype',
            field=models.CharField(max_length=50, blank=True, verbose_name='Тип челнока'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_software',
            field=models.TextField(verbose_name='Возможности встроенного ПО', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_speedcontrol',
            field=models.CharField(max_length=50, blank=True, verbose_name='Регулятор (ограничитель) скорости'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_spool',
            field=models.CharField(max_length=50, blank=True, verbose_name='Горизонтальное расположение катушки'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_startstop',
            field=models.CharField(max_length=255, blank=True, verbose_name='Клавиша шитья без педали'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_stitchlenght',
            field=models.CharField(max_length=50, blank=True, verbose_name='Максимальная длина стежка, мм'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_stitchquantity',
            field=models.SmallIntegerField(default=0, verbose_name='Количество строчек'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_stitchwidth',
            field=models.CharField(max_length=50, blank=True, verbose_name='Максимальная ширина строчки, мм'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_threader',
            field=models.CharField(max_length=50, blank=True, verbose_name='Нитевдеватель'),
        ),
        migrations.AddField(
            model_name='product',
            name='sm_threader_bool',
            field=models.BooleanField(default=False, verbose_name='Есть нитевдеватель'),
        ),
        migrations.AddField(
            model_name='product',
            name='spec',
            field=models.TextField(verbose_name='Подробное описание', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='spprice',
            field=models.PositiveIntegerField(default=0, verbose_name='Цена СП'),
        ),
        migrations.AddField(
            model_name='product',
            name='state',
            field=models.TextField(verbose_name='Состояние', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='stitches',
            field=models.TextField(verbose_name='Строчки', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='suspend',
            field=models.BooleanField(default=False, verbose_name='Готовится к выпуску'),
        ),
        migrations.AddField(
            model_name='product',
            name='sw_datalink',
            field=models.CharField(max_length=255, blank=True, verbose_name='Способ связи с компьютером'),
        ),
        migrations.AddField(
            model_name='product',
            name='sw_hoopsize',
            field=models.CharField(max_length=255, blank=True, verbose_name='Размер пяльцев'),
        ),
        migrations.AddField(
            model_name='product',
            name='swcode',
            field=models.CharField(max_length=20, blank=True, verbose_name='Код товара в ШМ'),
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.FloatField(default=0, verbose_name='Вес нетто'),
        ),
        migrations.AddField(
            model_name='product',
            name='whatis',
            field=models.TextField(verbose_name='Что это такое', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='whatisit',
            field=models.CharField(max_length=50, blank=True, verbose_name='Что это такое, кратко'),
        ),
        migrations.AddField(
            model_name='product',
            name='yandexdescr',
            field=models.TextField(verbose_name='Описание для Яндекс.Маркет', blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.SmallIntegerField(default=1, choices=[(1, 'наличные'), (2, 'банковская карта'), (3, 'банковский перевод'), (4, 'наложенный платёж')], verbose_name='оплата'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (512, 'доставлен в ТК'), (4096, 'консультация'), (8192, 'проблема'), (16384, 'завершен')], verbose_name='статус'),
        ),
    ]
