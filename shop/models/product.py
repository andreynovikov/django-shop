import logging
import os

from decimal import Decimal, ROUND_UP, ROUND_HALF_EVEN

from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.sites.models import Site
from django.db import connection, models
from django.db.models.signals import post_save
from django.utils.functional import cached_property
from django.urls import reverse

from mptt.models import TreeManyToManyField

from tagging.fields import TagField

from reviews.models import UserReviewAbstractModel, REVIEW_MAX_LENGTH

from django_better_admin_arrayfield.models.fields import ArrayField
from model_field_list import ModelFieldListField

from . import Category, Country, Currency, Manufacturer, SalesAction, Supplier

__all__ = [
    'Product', 'ProductImage', 'ProductRelation', 'ProductSet', 'ProductKind', 'ProductReview', 'Stock'
]

logger = logging.getLogger(__name__)


def product_image_path(instance, filename):
    _, extension = os.path.splitext(filename)
    return 'products/{0}/{1}{2}'.format(instance.manufacturer.code, instance.code, extension)


def product_big_image_path(instance, filename):
    _, extension = os.path.splitext(filename)
    return 'products/{0}/{1}.b{2}'.format(instance.manufacturer.code, instance.code, extension)


class Product(models.Model):
    code = models.CharField('идентификатор', max_length=20, unique=True, db_index=True)
    article = models.CharField('код 1С', max_length=20, blank=True, db_index=True)
    partnumber = models.CharField('partnumber', max_length=200, blank=True, db_index=True)
    gtin = models.CharField('штрих-код', max_length=17, blank=True, db_index=True)
    gtins = ArrayField(models.CharField(max_length=255, blank=True), verbose_name='дополнительные штих-коды', default=list, blank=True, db_index=True)
    tnved = models.CharField('ТН ВЭД', max_length=16, blank=True)
    enabled = models.BooleanField('включён', default=False, db_index=True)
    title = models.CharField('название', max_length=200, db_index=True)
    price = models.DecimalField('цена, руб', max_digits=10, decimal_places=2, default=0, db_index=True)
    cur_price = models.DecimalField('цена, вал', max_digits=10, decimal_places=2, default=0)
    cur_code = models.ForeignKey(Currency, verbose_name='валюта', related_name="rtprice", on_delete=models.PROTECT, default=643)
    ws_price = models.DecimalField('опт. цена, руб', max_digits=10, decimal_places=2, default=0)
    ws_cur_price = models.DecimalField('опт. цена, вал', max_digits=10, decimal_places=2, default=0)
    ws_cur_code = models.ForeignKey(Currency, verbose_name='опт. валюта', related_name="wsprice", on_delete=models.PROTECT, default=643)
    ws_pack_only = models.BooleanField('опт. только упаковкой', default=False)
    sp_price = models.DecimalField('цена СП, руб', max_digits=10, decimal_places=2, default=0)
    sp_cur_price = models.DecimalField('цена СП, вал', max_digits=10, decimal_places=2, default=0)
    sp_cur_code = models.ForeignKey(Currency, verbose_name='СП валюта', related_name="spprice", on_delete=models.PROTECT, default=643)
    pct_discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    val_discount = models.DecimalField('скидка, руб', max_digits=10, decimal_places=2, default=0)
    ws_pct_discount = models.PositiveSmallIntegerField('опт. скидка, %', default=0)
    max_discount = models.PositiveSmallIntegerField('макс. скидка, %', default=10)
    # todo: not used in logic, only in templates
    max_val_discount = models.DecimalField('макс. скидка, руб', max_digits=10, decimal_places=2, null=True, blank=True)
    ws_max_discount = models.PositiveSmallIntegerField('опт. макс. скидка, %', default=10)
    image = models.ImageField('изображение', upload_to=product_image_path, max_length=255, null=True, blank=True)
    big_image = models.ImageField('большое изображение', upload_to=product_big_image_path, max_length=255, null=True, blank=True)
    kind = models.ManyToManyField('shop.ProductKind', verbose_name='тип', related_name='products',
                                  related_query_name='product', blank=True)
    categories = TreeManyToManyField('shop.Category', related_name='products',
                                     related_query_name='product', verbose_name='категории', blank=True)
    tags = TagField('теги')
    forbid_price_import = models.BooleanField('не импортировать цену', default=False)
    forbid_ws_price_import = models.BooleanField('не импортировать опт. цену', default=False)
    service_life = models.PositiveSmallIntegerField('срок службы, мес', default=60)
    warranty = models.PositiveSmallIntegerField('гарантия, мес', default=0)
    extended_warranty = models.CharField('расширенная гарантия', max_length=20, blank=True)
    manufacturer_warranty = models.BooleanField('официальная гарантия', default=False)
    comment_warranty = models.CharField('комментарий к гарантии', max_length=200, blank=True)

    swcode = models.CharField('Код товара в ШМ', max_length=20, blank=True)
    runame = models.CharField('Русское название', max_length=200, blank=True)
    sales_notes = models.CharField('Yandex.Market Sales Notes', max_length=128, blank=True)
    bid = models.CharField('Ставка маркета для основной выдачи', max_length=10, blank=True)
    cbid = models.CharField('Ставка маркета для карточки модели', max_length=10, blank=True)
    show_on_sw = models.BooleanField('витрина', default=True, db_index=True)
    gift = models.BooleanField('Годится в подарок', default=False)
    merchant = models.BooleanField('мерчант', default=False, db_index=True)
    market = models.BooleanField('маркет', default=False, db_index=True)
    manufacturer = models.ForeignKey(Manufacturer, verbose_name="Производитель", on_delete=models.PROTECT, default=49)
    country = models.ForeignKey(Country, verbose_name="Страна производства", on_delete=models.PROTECT, default=1)
    developer_country = models.ForeignKey(Country, verbose_name="Страна разработки", on_delete=models.PROTECT, related_name="developed_product", default=1)
    isnew = models.BooleanField('Новинка', default=False)
    deshevle = models.BooleanField('Нашли дешевле', default=False)
    recomended = models.BooleanField('Рекомендуем', default=False)
    absent = models.BooleanField('Нет в продаже', default=False)
    credit_allowed = models.BooleanField('можно в кредит', default=False)
    present = models.CharField('Подарок к этому товару', max_length=255, blank=True)
    coupon = models.BooleanField('Предлагать купон', default=False)
    not_for_sale = models.BooleanField('Не показывать кнопку заказа', default=False)
    firstpage = models.BooleanField('Показать на первой странице', default=False)
    suspend = models.BooleanField('Готовится к выпуску', default=False)
    preorder = models.BooleanField('предзаказ', default=False)
    order = models.IntegerField('позиция сортировки', default=0, db_index=True)
    opinion = models.CharField('Ссылка на обсуждение модели', max_length=255, blank=True)
    allow_reviews = models.BooleanField('Разрешить обзоры', default=True)
    measure = models.CharField('Единицы', max_length=10, blank=True)
    weight = models.FloatField('Вес без упаковки, кг', default=0)
    length = models.DecimalField('длина, см', max_digits=5, decimal_places=2, default=0)
    width = models.DecimalField('ширина, см', max_digits=5, decimal_places=2, default=0)
    height = models.DecimalField('высота, см', max_digits=5, decimal_places=2, default=0)
    delivery = models.SmallIntegerField('Доставка', default=0)
    consultant_delivery_price = models.DecimalField('Стоимость доставки с консультантом', max_digits=6, decimal_places=2, default=0)
    spec = models.TextField('Подробное описание', blank=True)
    descr = models.TextField('Краткое описание', blank=True)
    state = models.TextField('Состояние', blank=True)
    manuals = models.TextField('инструкции', blank=True)
    stitches = models.TextField('Строчки', blank=True)
    complect = models.TextField('Комплектация', blank=True)
    dealertxt = models.TextField('Текст про официального дилера', blank=True)
    num = models.IntegerField('в наличии', default=-1)
    stock = models.ManyToManyField(Supplier, through='Stock')
    pack_factor = models.SmallIntegerField('Количество в упаковке', default=1)
    shortdescr = models.TextField('Характеристика', blank=True)
    yandexdescr = models.TextField('Описание для Яндекс.Маркет', blank=True)
    whatis = models.TextField('Что это такое', blank=True)
    whatisit = models.CharField('Что это такое, кратко', max_length=50, blank=True)
    variations = models.CharField('вариации', max_length=255, blank=True)
    comment_packer = models.CharField('комментарий для сборщика', max_length=255, blank=True)

    sales_actions = models.ManyToManyField(SalesAction, related_name='products', related_query_name='product', verbose_name='акции', blank=True)
    related = models.ManyToManyField('self', through='ProductRelation', symmetrical=False, blank=True)
    constituents = models.ManyToManyField('self', through='ProductSet', related_name='+', symmetrical=False, blank=True)
    recalculate_price = models.BooleanField('пересчитывать цену', default=True)
    hide_contents = models.BooleanField('скрыть содержимое', default=True)

    fabric_verylite = models.CharField('Очень легкие ткани', max_length=50, blank=True)
    fabric_lite = models.CharField('Легкие ткани', max_length=50, blank=True)
    fabric_medium = models.CharField('Средние ткани', max_length=50, blank=True)
    fabric_hard = models.CharField('Тяжелые ткани', max_length=50, blank=True)
    fabric_veryhard = models.CharField('Очень тяжелые ткани', max_length=50, blank=True)
    fabric_stretch = models.CharField('Трикотаж', max_length=50, blank=True)
    fabric_leather = models.CharField('Кожа', max_length=50, blank=True)
    sm_shuttletype = models.CharField('Тип челнока', max_length=50, blank=True)
    sm_stitchwidth = models.CharField('Максимальная ширина строчки, мм', max_length=50, blank=True)
    sm_stitchlenght = models.CharField('Максимальная длина стежка, мм', max_length=50, blank=True)
    sm_stitchquantity = models.SmallIntegerField('Количество строчек', default=0)
    sm_buttonhole = models.CharField('Режим вымётывания петли', max_length=255, blank=True)
    sm_dualtransporter = models.CharField('Верхний транспортёр', max_length=50, blank=True)
    sm_platformlenght = models.CharField('Длина платформы, см', max_length=50, blank=True)
    sm_freearm = models.CharField('Размеры рукавной платформы (длина/обхват), см', max_length=50, blank=True)
    ov_freearm = models.CharField('Рукавная платформа', max_length=255, blank=True)
    sm_feedwidth = models.CharField('Ширина гребёнки транспортера, мм', max_length=50, blank=True)
    sm_footheight = models.CharField('Высота подъема лапки (нормальная/максимальная)', max_length=50, blank=True)
    sm_constant = models.CharField('Электронный стабилизатор усилия прокола', max_length=50, blank=True)
    sm_speedcontrol = models.CharField('Регулятор (ограничитель) максимальной скорости', max_length=50, blank=True)
    sm_needleupdown = models.CharField('Программируемая остановка иглы в верхнем/нижнем положении', max_length=50, blank=True)
    sm_threader = models.CharField('Нитевдеватель', max_length=50, blank=True)
    sm_spool = models.CharField('Горизонтальное расположение катушки', max_length=50, blank=True)
    sm_presscontrol = models.CharField('Регулятор давления лапки', max_length=50, blank=True)
    sm_power = models.FloatField('Потребляемая мощность, Вт', default=0)
    sm_light = models.CharField('Тип освещения', max_length=50, blank=True)
    sm_organizer = models.CharField('Органайзер', max_length=50, blank=True)
    sm_autostop = models.CharField('Автостоп при намотке нитки на шпульку', max_length=50, blank=True)
    sm_ruler = models.CharField('Линейка на корпусе', max_length=50, blank=True)
    sm_wastebin = models.CharField('мусоросборник', max_length=50, blank=True)
    sm_cover = models.CharField('Чехол', max_length=50, blank=True)
    sm_startstop = models.CharField('Клавиша шитья без педали', max_length=255, blank=True)
    sm_kneelift = models.CharField('Коленный рычаг подъема лапки', max_length=255, blank=True)
    sm_display = models.TextField('Дисплей', blank=True)
    sm_advisor = models.CharField('Швейный советник', max_length=255, blank=True)
    sm_memory = models.CharField('Память', max_length=255, blank=True)
    sm_mirror = models.CharField('Зеркальное отображение образца строчки', max_length=255, blank=True)
    sm_fix = models.CharField('Закрепка', max_length=255, blank=True)
    sm_alphabet = models.CharField('Алфавит', max_length=255, blank=True)
    sm_diffeed = models.CharField('Дифференциальный транспортер ткани', max_length=255, blank=True)
    sm_easythreading = models.CharField('Облегчённая заправка петлителей', max_length=255, blank=True)
    sm_needles = models.CharField('Стандарт игл', max_length=255, blank=True)
    sm_software = models.TextField('Возможности встроенного ПО', blank=True)
    sm_autocutter = models.CharField('Автоматическая обрезка нитей', max_length=255, blank=True)
    sm_maxi = models.CharField('Макси-узоры', max_length=255, blank=True)
    sm_autobuttonhole_bool = models.BooleanField('Делает автоматически петлю', default=False)
    sm_threader_bool = models.BooleanField('Есть нитевдеватель', default=False)
    sm_dualtransporter_bool = models.BooleanField('Есть встроенный транспортер', default=False)
    sm_alphabet_bool = models.BooleanField('Есть алфавит', default=False)
    sm_maxi_bool = models.BooleanField('Есть макси-узоры', default=False)
    sm_patterncreation_bool = models.BooleanField('Есть функция создания строчек', default=False)
    sm_advisor_bool = models.BooleanField('Есть швейный советник', default=False)
    km_class = models.CharField('Класс машины', max_length=255, blank=True)
    km_font = models.CharField('Количество фонтур', max_length=255, blank=True)
    km_needles = models.CharField('Количество игл', max_length=255, blank=True)
    km_prog = models.CharField('Способ программирования', max_length=255, blank=True)
    km_rapport = models.CharField('Раппорт программируемого рисунка', max_length=255, blank=True)
    sw_hoopsize = models.CharField('Размер пяльцев', max_length=255, blank=True)
    sw_datalink = models.CharField('Способ связи с компьютером', max_length=255, blank=True)
    prom_transporter_type = models.CharField('Тип транспортера', max_length=255, blank=True)
    prom_shuttle_type = models.CharField('Тип челнока', max_length=255, blank=True)
    prom_speed = models.CharField('Максимальная скорость шитья', max_length=255, blank=True)
    prom_needle_type = models.CharField('Размер и тип иглы', max_length=255, blank=True)
    prom_stitch_lenght = models.CharField('Длина стежка', max_length=255, blank=True)
    prom_foot_lift = models.CharField('Высота подъема лапки', max_length=255, blank=True)
    prom_fabric_type = models.CharField('Тип материала', max_length=255, blank=True)
    prom_oil_type = models.CharField('Тип смазки', max_length=255, blank=True)
    prom_weight = models.FloatField('Вес с упаковкой, кг', default=0)
    prom_cutting = models.CharField('Обрезка нити', max_length=255, blank=True)
    prom_threads_num = models.CharField('Количество нитей', max_length=255, blank=True)
    prom_power = models.CharField('Мощность', max_length=255, blank=True)
    prom_bhlenght = models.CharField('Длина петли', max_length=255, blank=True)
    prom_overstitch_lenght = models.CharField('Максимальная длина обметочного стежка', max_length=255, blank=True)
    prom_overstitch_width = models.CharField('Максимальная ширина обметочного стежка', max_length=255, blank=True)
    prom_stitch_width = models.CharField('Ширина зигзагообразной строчки', max_length=255, blank=True)
    prom_needle_width = models.CharField('Расстояние между иглами', max_length=255, blank=True)
    prom_needle_num = models.CharField('Количество игл', max_length=255, blank=True)
    prom_platform_type = models.CharField('Тип платформы', max_length=255, blank=True)
    prom_button_diaouter = models.CharField('Наружный диаметр пуговицы', max_length=255, blank=True)
    prom_button_diainner = models.CharField('Внутренний диаметр пуговицы', max_length=255, blank=True)
    prom_needle_height = models.CharField('Ход игловодителя', max_length=255, blank=True)
    prom_stitch_type = models.CharField('Тип стежка', max_length=255, blank=True)
    prom_autothread = models.CharField('Автоматический нитеотводчик', max_length=255, blank=True)

    fts_vector = SearchVectorField(null=True)

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['title']
        indexes = [
            GinIndex(fields=['fts_vector'])
        ]

    def get_absolute_url(self):
        return reverse('product', args=[str(self.code)])

    def save(self, *args, **kwargs):
        if self.pk is None or self.constituents.count() == 0 or not self.recalculate_price:
            self.price = self.cur_price * self.cur_code.rate
            self.ws_price = self.ws_cur_price * self.ws_cur_code.rate
            self.sp_price = self.sp_cur_price * self.sp_cur_code.rate
        else:
            self.update_set_price()
        super(Product, self).save(*args, **kwargs)
        self.update_fts_vector()
        self.update_sets()

    def update_sets(self):
        product_sets = ProductSet.objects.filter(constituent=self)
        for product_set in product_sets:
            updated = False
            if self.num < 0:
                product_set.declaration.num = -1
                updated = True
            if product_set.declaration.recalculate_price:
                product_set.declaration.update_set_price()
                updated = True
            if updated:
                product_set.declaration.save()

    def update_set_price(self):
        price = Decimal('0')
        ws_price = Decimal('0')
        sp_price = Decimal('0')
        constituents = ProductSet.objects.filter(declaration=self)
        for item in constituents:
            item_price = item.constituent.price
            item_ws_price = item.constituent.ws_price
            item_sp_price = item.constituent.sp_price
            if item.discount > 0:
                discount = Decimal((100 - item.discount) / 100)
                item_price = (item_price * discount).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
                item_ws_price = (item_ws_price * discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
                item_sp_price = (item_sp_price * discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
            price = price + item_price * item.quantity
            ws_price = ws_price + item_ws_price * item.quantity
            sp_price = sp_price + item_sp_price * item.quantity

        self.price = price
        self.ws_price = ws_price
        self.sp_price = sp_price

    def update_fts_vector(self):
        language = 'russian'
        vector = SearchVector('title', 'code', 'article', 'partnumber', weight='A', config=language)
        vector = vector + SearchVector('whatis', 'shortdescr', weight='B', config=language)
        vector = vector + SearchVector('descr', 'spec', weight='D', config=language)
        Product.objects.filter(id=self.id).update(fts_vector=vector)  # use direct DB update to skip heavy save() logic

    # TODO: depricated
    def get_sales_actions(self):
        return self.sales_actions.filter(active=True, sites=Site.objects.get_current()).order_by('order')

    @cached_property
    def breadcrumbs(self):
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        # select (optionally) not hidden category, the deepest or first sibling
        category = self.categories.filter(tree_id=root.tree_id, active=True).order_by('hidden', '-level', 'lft').first()
        if category:
            return category.get_ancestors(include_self=True)
        return None

    @property
    def markup(self):
        if self.price > 0 and self.sp_price > 0:
            return int((self.price - self.sp_price) / self.price * 100)
        else:
            return 0

    @property
    def cost(self):
        return self.price - self.discount

    @property
    def discount(self):
        pd = Decimal(0)
        if self.pct_discount > 0:
            price = self.price.quantize(Decimal('1'), rounding=ROUND_UP)
            pd = (price * Decimal(self.pct_discount / 100)).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        if self.val_discount > pd:
            pd = self.val_discount
        return pd

    @property
    def ws_cost(self):
        return self.ws_price - self.ws_discount

    @property
    def ws_discount(self):
        if self.ws_pct_discount > 0:
            return (self.ws_price * Decimal(self.ws_pct_discount / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        else:
            return Decimal(0)

    @property
    def instock(self):
        if self.num >= 0:
            return self.num
        self.num = self.get_stock()
        super(Product, self).save()
        return self.num

    def get_stock(self, integration=None, express=False):
        num = 0
        if self.constituents.count() == 0:
            if integration is not None:
                suppliers = self.stock.filter(pk__in=integration.suppliers.all())
            else:
                suppliers = self.stock.filter(count_in_stock=Supplier.COUNT_STOCK)

            if express:
                suppliers = suppliers.filter(express_count_in_stock=Supplier.COUNT_STOCK)

            if suppliers.exists():
                for supplier in suppliers:
                    stock = Stock.objects.get(product=self, supplier=supplier)
                    num = num + stock.quantity + stock.correction

            if num > 0:
                sites = [Site.objects.get(domain='www.sewing-world.ru').id]
                sites.extend(Site.objects.filter(integration__suppliers__in=suppliers).distinct().values_list('id', flat=True))
                if Supplier.objects.filter(count_in_stock=Supplier.COUNT_STOCK, pk__in=suppliers).count():
                    sites.extend(Site.objects.filter(integration__isnull=True).values_list('id', flat=True))
                site_addon = 'IN ({})'.format(','.join(map(str, sites)))
                cursor = connection.cursor()
                cursor.execute("""SELECT SUM(shop_orderitem.quantity) AS quantity FROM shop_orderitem
                              INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
                              AND shop_order.site_id """ + site_addon + """ AND shop_orderitem.product_id = %s GROUP BY
                              shop_orderitem.product_id""", (self.id,))
                if cursor.rowcount:
                    row = cursor.fetchone()
                    num = num - float(row[0])
                cursor.close()
                if num < 0:
                    num = 0
        else:
            num = 32767
            for item in ProductSet.objects.filter(declaration=self):
                n = item.constituent.instock
                if item.quantity > 1:
                    n = int(n / item.quantity)
                if n < num:
                    num = n
        return num

    @staticmethod
    def autocomplete_search_fields():
        return ['title__icontains', 'code__icontains', 'article__icontains', 'partnumber__icontains']

    def __str__(self):
        # return " ".join([self.partnumber, self.title])
        return self.title


def product_extra_image_path(instance, filename):
    logger.error("IMAGE {} {}".format(filename, instance.order))
    return 'products/{0}/{1}/{2}'.format(instance.product.manufacturer.code, instance.product.code, filename)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('изображение', upload_to=product_extra_image_path, max_length=255)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'изображение товара'
        verbose_name_plural = 'изображения товара'
        ordering = ['order']


class ProductRelation(models.Model):
    KIND_SIMILAR = 1
    KIND_ACCESSORY = 2
    KIND_GIFT = 3
    RELATIONSHIP_KINDS = (
        (KIND_SIMILAR, 'похожий'),
        (KIND_ACCESSORY, 'аксессуар'),
        (KIND_GIFT, 'подарок'),
    )
    parent_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='parent_products', verbose_name='товар')
    child_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='child_products', verbose_name='связанный товар')
    kind = models.SmallIntegerField('тип', choices=RELATIONSHIP_KINDS, default=KIND_SIMILAR, db_index=True)

    class Meta:
        verbose_name = 'связанный товар'
        verbose_name_plural = 'связанные товары'


class ProductSet(models.Model):
    declaration = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='set_constituents', verbose_name='определение')
    constituent = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='set_declarations', verbose_name='составляющая')
    quantity = models.PositiveSmallIntegerField('кол-во', default=1)
    discount = models.PositiveSmallIntegerField('скидка, %', default=0)

    class Meta:
        verbose_name = 'комплект'
        verbose_name_plural = 'комплекты'


class ProductKind(models.Model):
    name = models.CharField('Название', max_length=100)
    comparison = ModelFieldListField('критерии сравнения', source_model=Product, blank=True)

    class Meta:
        verbose_name = 'тип товара'
        verbose_name_plural = 'типы товаров'

    def __str__(self):
        return self.name


class ProductReview(UserReviewAbstractModel):
    advantage = models.TextField('достоинства', max_length=REVIEW_MAX_LENGTH, blank=True)
    disadvantage = models.TextField('недостатки', max_length=REVIEW_MAX_LENGTH, blank=True)
    comment = models.TextField('комментарий', max_length=REVIEW_MAX_LENGTH, blank=True)
    reviewer_name = models.CharField('имя пользователя', max_length=100, blank=True)
    reviewer_avatar = models.CharField('аватар пользователя', max_length=255, blank=True)


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items', related_query_name='stock_item')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='поставщик')
    quantity = models.FloatField('кол-во', default=0)
    correction = models.FloatField('коррекция', default=0)
    reason = models.CharField('причина', max_length=100, blank=True)

    class Meta:
        verbose_name = 'запас'
        verbose_name_plural = 'запасы'
        unique_together = ('product', 'supplier')


def update_product_prices(sender, instance, **kwargs):
    products = Product.objects.filter(models.Q(cur_code=instance) | models.Q(ws_cur_code=instance))
    for product in products:
        product.save()


post_save.connect(update_product_prices, sender=Currency, dispatch_uid='update_product_prices')
