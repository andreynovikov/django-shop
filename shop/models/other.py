import re
import datetime
import logging

from decimal import Decimal, ROUND_UP, ROUND_HALF_EVEN

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.sites.models import Site
from django.db import connection, models
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.functional import cached_property
from django.urls import reverse

from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField

from tagging.fields import TagField

from reviews.models import UserReviewAbstractModel, REVIEW_MAX_LENGTH

from model_field_list import ModelFieldListField

__all__ = [
    'ShopUserManager', 'ShopUser', 'Category', 'Currency', 'Country', 'Region', 'City',
    'Supplier', 'Store', 'ServiceCenter', 'Manufacturer', 'Advert', 'SalesAction',
    'Product', 'ProductRelation', 'ProductSet', 'ProductKind', 'Stock', 'ProductReview',
    'Basket', 'BasketItem'
]

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


class ShopUserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError('Users must have a phone')

        user = self.model(phone=self.normalize_phone(phone),)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password):
        user = self.create_user(phone, password=password,)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_phone(phone):
        phone = re.sub(r"[^0-9\+]", "", phone)
        if not phone.startswith("+"):
            phone = "+7" + phone
        return phone

    @staticmethod
    def format_phone(phone):
        m = re.match(r"(\+7)(\d{3})(\d{3})(\d{2})(\d{2})", phone)
        if not m:
            m = re.match(r"(\+7)(\d{3})(\d.{2})(.{2})(\d{2})", phone)
            if not m:
                return phone
        return "{0} ({1}) {2}-{3}-{4}".format(*m.groups())


class AliasField(models.Field):
    def contribute_to_class(self, cls, name, private_only=False):
        ''' virtual_only is deprecated in favor of private_only '''
        super(AliasField, self).contribute_to_class(cls, name, private_only=True)
        setattr(cls, name, self)


class UsernameField(models.CharField):
    description = "CharField that stores NULL but returns ''"

    def __init__(self, *args, **kwargs):
        kwargs['unique'] = True
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['default'] = ''
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['unique']
        del kwargs['null']
        del kwargs['blank']
        del kwargs['default']
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        return value or ''

    def get_db_prep_value(self, value, connection, prepared=False):
        return value or None


class ShopUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField('телефон', max_length=30, unique=True)
    name = models.CharField('имя', max_length=100, blank=True)
    username = UsernameField('прозвище', max_length=100)
    email = models.EmailField('эл.почта', blank=True)
    postcode = models.CharField('индекс', max_length=10, blank=True)
    city = models.CharField('город', max_length=255, blank=True)
    address = models.CharField('адрес', max_length=255, blank=True)
    discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    is_active = models.BooleanField('активный', default=True)
    is_staff = models.BooleanField('сотрудник', default=False)
    permanent_password = models.BooleanField('постоянный пароль', default=False)
    date_joined = models.DateTimeField('дата регистрации', default=timezone.now)
    tags = TagField('теги')
    first_name = AliasField(db_column='name')
    last_name = AliasField(db_column='name')

    objects = ShopUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        permissions = (
            ('wholesale', "Может покупать оптом"),
        )

    @staticmethod
    def autocomplete_search_fields():
        return ['id__iexact', 'name__icontains', 'phone__icontains', 'email__icontains']

    def get_short_name(self):
        return self.name or self.phone

    def get_full_name(self):
        return self.username or self.name or ShopUserManager.format_phone(self.phone[:-6] + '****' + self.phone[-2:])

    def __str__(self):
        return self.get_short_name()

    def related_label(self):
        if self.name:
            return "%s (%s)" % (self.name, self.phone)
        else:
            return self.phone


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.PROTECT)
    active = models.BooleanField('включена', default=True, db_index=True)
    hidden = models.BooleanField('спрятана', default=False, db_index=True)
    filters = models.CharField('фильтры', max_length=255, blank=True)
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    image = models.ImageField('изображение', upload_to='categories', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    promo_image = models.ImageField('промо изображение', upload_to='categories', blank=True,
                                    width_field='promo_image_width', height_field='promo_image_height')
    promo_image_width = models.IntegerField(null=True, blank=True)
    promo_image_height = models.IntegerField(null=True, blank=True)
    product_order = models.CharField('поле сортировки товаров', max_length=50, default='-price')
    ya_active = models.BooleanField('выдавать в Яндекс.Маркет', default=True)

    def get_active_descendants(self):
        return self.get_descendants().filter(active=True)

    def get_absolute_url(self):
        return reverse('category', kwargs={'path': self.get_path()})

    def __str__(self):
        # return self.name
        show_path = False
        import traceback
        tb = traceback.extract_stack(limit=6)
        for line in tb:
            # if self.id == 15:
            #     import sys
            #     print('{}: {}'.format(line.filename, line.name), file=sys.stderr)
            if line.name == 'field_choices' and line.filename.endswith('contrib/admin/filters.py'):
                show_path = True
            if line.name == 'get' and line.filename.endswith('contrib/admin/views/autocomplete.py'):
                show_path = True
        if show_path:
            return '/'.join([x['name'] for x in self.get_ancestors(include_self=True).values()])
        else:
            return self.name

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"


class Currency(models.Model):
    code = models.PositiveSmallIntegerField('код', primary_key=True)
    name = models.CharField('название', max_length=20)
    rate = models.DecimalField('курс', max_digits=5, decimal_places=2, default=1)

    class Meta:
        verbose_name = 'валюта'
        verbose_name_plural = 'валюты'

    def __str__(self):
        return self.name


def update_product_prices(sender, instance, **kwargs):
    products = Product.objects.filter(models.Q(cur_code=instance) | models.Q(ws_cur_code=instance))
    for product in products:
        product.save()


post_save.connect(update_product_prices, sender=Currency, dispatch_uid='update_product_prices')


class Country(models.Model):
    name = models.CharField('название', max_length=100)
    ename = models.CharField('англ. название', max_length=100)
    enabled = models.BooleanField('включена', default=True)

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField('название', max_length=100)
    country = models.ForeignKey(Country, verbose_name='страна', on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'регион'
        verbose_name_plural = 'регионы'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return str(self.country) + ', ' + self.name


class City(models.Model):
    country = models.ForeignKey(Country, verbose_name='страна', on_delete=models.PROTECT)
    region = models.ForeignKey(Region, verbose_name='регион', blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField('название', max_length=100)
    ename = models.CharField('англ. название', max_length=100, blank=True)
    latitude = models.FloatField('широта', default=0, blank=True, null=True)
    longitude = models.FloatField('долгота', default=0, blank=True, null=True)
    code = models.CharField('код', max_length=20, blank=True)

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'
        ordering = ('country', 'name')

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return str(self.country) + ', ' + self.name


class Supplier(models.Model):
    COUNT_STOCK = 1
    COUNT_DEFER = 2
    COUNT_NONE = 99
    COUNT_CHOICES = (
        (COUNT_NONE, 'не учитывать'),
        (COUNT_STOCK, 'наличие'),
        (COUNT_DEFER, 'под заказ'),
    )
    code = models.CharField('код', max_length=10)
    code1c = models.CharField('код 1С', max_length=50)
    name = models.CharField('название', max_length=100)
    show_in_order = models.BooleanField('показывать в заказе', default=False, db_index=True)
    count_in_stock = models.SmallIntegerField('учитывать в наличии', choices=COUNT_CHOICES, default=COUNT_NONE)
    spb_count_in_stock = models.SmallIntegerField('учитывать в наличии СПб', choices=COUNT_CHOICES, default=COUNT_NONE)
    ws_count_in_stock = models.SmallIntegerField('учитывать в наличии Опт', choices=COUNT_CHOICES, default=COUNT_NONE)
    beru_count_in_stock = models.SmallIntegerField('учитывать в наличии Беру', choices=COUNT_CHOICES, default=COUNT_NONE)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'
        ordering = ['order']

    @staticmethod
    def autocomplete_search_fields():
        return ['code__startswith', 'name__icontains']

    def __str__(self):
        return self.name


class Store(models.Model):
    city = models.ForeignKey(City, verbose_name='город', on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, verbose_name='склад', related_name='stores', blank=True, null=True, on_delete=models.SET_NULL)
    address = models.CharField('адрес', max_length=255)
    phone = models.CharField('телефон', max_length=100, blank=True)
    name = models.CharField('название', max_length=100)
    enabled = models.BooleanField('включён', default=True)
    description = models.TextField('описание', blank=True)
    latitude = models.FloatField('широта', default=0, blank=True, null=True)
    longitude = models.FloatField('долгота', default=0, blank=True, null=True)
    postcode = models.CharField('индекс', max_length=20, blank=True)
    address2 = models.CharField('доп.адрес', max_length=255, blank=True)
    phone2 = models.CharField('доп.телефон', max_length=100, blank=True)
    url = models.CharField('сайт', max_length=100, blank=True)
    email = models.CharField('эл.адрес', max_length=100, blank=True)
    hours = models.CharField('раб.часы', max_length=100, blank=True)
    logo = models.CharField('логотип', max_length=30, blank=True)
    payment_cash = models.BooleanField('наличные', default=False)
    payment_visa = models.BooleanField('visa', default=False)
    payment_master = models.BooleanField('mastercard', default=False)
    payment_mir = models.BooleanField('мир', default=False)
    payment_credit = models.BooleanField('кредит', default=False)

    class Meta:
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'
        ordering = ('city', 'address')

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains', 'address__icontains', 'city__name__icontains']

    def get_absolute_url(self):
        return reverse('store', args=[str(self.pk)])

    def __str__(self):
        return str(self.city) + ', ' + self.address


class ServiceCenter(models.Model):
    city = models.ForeignKey(City, verbose_name='город', on_delete=models.PROTECT)
    address = models.CharField('адрес', max_length=255)
    phone = models.CharField('телефон', max_length=100, blank=True)
    enabled = models.BooleanField('включён', default=True)
    latitude = models.FloatField('широта', default=0, blank=True, null=True)
    longitude = models.FloatField('долгота', default=0, blank=True, null=True)

    class Meta:
        verbose_name = 'сервис-центр'
        verbose_name_plural = 'сервис-центры'
        ordering = ('city', 'address')

    @staticmethod
    def autocomplete_search_fields():
        return ['address__icontains', 'city__name__icontains']

    def __str__(self):
        return str(self.city) + ', ' + self.address


class Manufacturer(models.Model):
    code = models.CharField('код', max_length=30)
    name = models.CharField('название', max_length=150)
    machinemaker = models.BooleanField('машины делает', default=False)
    accessorymaker = models.BooleanField('аксессуары делает', default=False)
    logo = models.FileField('логотип', upload_to='logos', blank=True)
    logo_width = models.IntegerField(null=True, blank=True)
    logo_height = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'производитель'
        verbose_name_plural = 'производители'
        ordering = ['name']

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name


class Advert(models.Model):
    name = models.CharField('название', max_length=100)
    place = models.CharField('место', max_length=100, db_index=True)
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    active = models.BooleanField('активная', db_index=True)
    content = models.TextField('содержимое')
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'реклама'
        verbose_name_plural = 'рекламы'
        ordering = ['order']

    def __str__(self):
        return self.name


class SalesAction(models.Model):
    name = models.CharField('название', max_length=100)
    slug = models.CharField(max_length=100, db_index=True)
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    active = models.BooleanField('активная')
    show_in_list = models.BooleanField('показывать в списке', default=True)
    show_products = models.BooleanField('показывать список товаров', default=True)
    notice = models.CharField('уведомление', max_length=50, blank=True)
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    image = models.ImageField('изображение', upload_to='actions', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'акция'
        verbose_name_plural = 'акции'
        ordering = ['order']

    def get_absolute_url(self):
        return reverse('sales_action', args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField('идентификатор', max_length=20, unique=True, db_index=True)
    article = models.CharField('код 1С', max_length=20, blank=True, db_index=True)
    partnumber = models.CharField('partnumber', max_length=200, blank=True, db_index=True)
    gtin = models.CharField('GTIN', max_length=17, blank=True, db_index=True)
    enabled = models.BooleanField('включён', default=False, db_index=True)
    title = models.CharField('название', max_length=200)
    price = models.DecimalField('цена, руб', max_digits=10, decimal_places=2, default=0, db_column=settings.SHOP_PRICE_DB_COLUMN)
    if settings.SHOP_PRICE_DB_COLUMN == 'price':
        spb_price = models.DecimalField('цена СПб, руб', max_digits=10, decimal_places=2, default=0)
    cur_price = models.DecimalField('цена, вал', max_digits=10, decimal_places=2, default=0)
    cur_code = models.ForeignKey(Currency, verbose_name='валюта', related_name="rtprice", on_delete=models.PROTECT, default=643)
    ws_price = models.DecimalField('опт. цена, руб', max_digits=10, decimal_places=2, default=0)
    ws_cur_price = models.DecimalField('опт. цена, вал', max_digits=10, decimal_places=2, default=0)
    ws_cur_code = models.ForeignKey(Currency, verbose_name='опт. валюта', related_name="wsprice", on_delete=models.PROTECT, default=643)
    ws_pack_only = models.BooleanField('опт. только упаковкой', default=False)
    sp_price = models.DecimalField('цена СП, руб', max_digits=10, decimal_places=2, default=0)
    sp_cur_price = models.DecimalField('цена СП, вал', max_digits=10, decimal_places=2, default=0)
    sp_cur_code = models.ForeignKey(Currency, verbose_name='СП валюта', related_name="spprice", on_delete=models.PROTECT, default=643)
    beru_price = models.DecimalField('цена Беру, руб', max_digits=10, decimal_places=2, default=0)
    pct_discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    val_discount = models.DecimalField('скидка, руб', max_digits=10, decimal_places=2, default=0)
    ws_pct_discount = models.PositiveSmallIntegerField('опт. скидка, %', default=0)
    max_discount = models.PositiveSmallIntegerField('макс. скидка, %', default=10)
    # todo: not used in logic, only in templates
    max_val_discount = models.DecimalField('макс. скидка, руб', max_digits=10, decimal_places=2, null=True, blank=True)
    ws_max_discount = models.PositiveSmallIntegerField('опт. макс. скидка, %', default=10)
    image_prefix = models.CharField('префикс изображения', max_length=200)
    kind = models.ManyToManyField('shop.ProductKind', verbose_name='тип', related_name='products',
                                  related_query_name='product', blank=True)
    categories = TreeManyToManyField('shop.Category', related_name='products',
                                     related_query_name='product', verbose_name='категории', blank=True)
    tags = TagField('теги')
    forbid_price_import = models.BooleanField('не импортировать цену', default=False)
    if settings.SHOP_PRICE_DB_COLUMN == 'price':
        forbid_spb_price_import = models.BooleanField('не импортировать цену СПб', default=False)
    forbid_ws_price_import = models.BooleanField('не импортировать опт. цену', default=False)
    warranty = models.CharField('гарантия', max_length=20, blank=True)
    extended_warranty = models.CharField('расширенная гарантия', max_length=20, blank=True)
    manufacturer_warranty = models.BooleanField('официальная гарантия', default=False)

    swcode = models.CharField('Код товара в ШМ', max_length=20, blank=True)
    runame = models.CharField('Русское название', max_length=200, blank=True)
    sales_notes = models.CharField('Yandex.Market Sales Notes', max_length=50, blank=True)
    bid = models.CharField('Ставка маркета для основной выдачи', max_length=10, blank=True)
    cbid = models.CharField('Ставка маркета для карточки модели', max_length=10, blank=True)
    show_on_sw = models.BooleanField('витрина', default=True, db_index=True, db_column=settings.SHOP_SHOW_DB_COLUMN)
    if settings.SHOP_SHOW_DB_COLUMN == 'show_on_sw':
        spb_show_in_catalog = models.BooleanField('витрина СПб', default=True, db_index=True)
    gift = models.BooleanField('Годится в подарок', default=False)
    merchant = models.BooleanField('мерчант', default=False, db_index=True)
    market = models.BooleanField('маркет', default=False, db_index=True, db_column=settings.SHOP_MARKET_DB_COLUMN)
    if settings.SHOP_MARKET_DB_COLUMN == 'market':
        spb_market = models.BooleanField('маркет СПб', default=False, db_index=True)
    beru = models.BooleanField('выгружать в Беру', default=False, db_index=True)
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
    num = models.IntegerField('в наличии', default=-1, db_column=settings.SHOP_STOCK_DB_COLUMN)
    if settings.SHOP_STOCK_DB_COLUMN == 'num':
        spb_num = models.IntegerField('в наличии СПб', default=-1)
        ws_num = models.IntegerField('в наличии Опт', default=-1)
    stock = models.ManyToManyField(Supplier, through='Stock')
    pack_factor = models.SmallIntegerField('Количество в упаковке', default=1)
    shortdescr = models.TextField('Характеристика', blank=True)
    yandexdescr = models.TextField('Описание для Яндекс.Маркет', blank=True)
    whatis = models.TextField('Что это такое', blank=True)
    whatisit = models.CharField('Что это такое, кратко', max_length=50, blank=True)
    variations = models.CharField('вариации', max_length=255, blank=True)

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

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def get_absolute_url(self):
        return reverse('product', args=[str(self.code)])

    def save(self, *args, **kwargs):
        if self.pk is None or self.constituents.count() == 0 or not self.recalculate_price:
            if settings.SHOP_PRICE_DB_COLUMN == 'price':
                self.price = self.cur_price * self.cur_code.rate
                if self.spb_price == 0 or not self.forbid_spb_price_import:
                    self.spb_price = self.price
            self.ws_price = self.ws_cur_price * self.ws_cur_code.rate
            self.sp_price = self.sp_cur_price * self.sp_cur_code.rate
        else:
            self.update_set_price()
        self.image_prefix = ''.join(['images/', self.manufacturer.code, '/', self.code])
        super(Product, self).save(*args, **kwargs)
        if settings.SHOP_PRICE_DB_COLUMN == 'price':
            self.update_sets()

    def update_sets(self):
        product_sets = ProductSet.objects.filter(constituent=self)
        for product_set in product_sets:
            updated = False
            if self.num < 0:
                product_set.declaration.num = -1
                product_set.declaration.spb_num = -1
                product_set.declaration.ws_num = -1
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
        self.spb_price = price
        self.ws_price = ws_price
        self.sp_price = sp_price

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
        return int((self.price - self.sp_price) / self.price * 100)

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

    def get_stock(self, which=settings.SHOP_STOCK_DB_COLUMN):
        num = 0
        if self.constituents.count() == 0:
            if which == 'spb_num':
                suppliers = self.stock.filter(spb_count_in_stock=Supplier.COUNT_STOCK)
                site_addon = '= 6'
            elif which == 'ws_num':
                suppliers = self.stock.filter(ws_count_in_stock=Supplier.COUNT_STOCK)
                site_addon = '<> 6'
            elif which == 'beru':
                suppliers = self.stock.filter(beru_count_in_stock=Supplier.COUNT_STOCK)
                site_addon = '<> 6'
            else:
                suppliers = self.stock.filter(count_in_stock=Supplier.COUNT_STOCK)
                site_addon = '<> 6'
            if suppliers.exists():
                for supplier in suppliers:
                    stock = Stock.objects.get(product=self, supplier=supplier)
                    num = num + stock.quantity + stock.correction

            # reserve 2 items for retail
            if num > 0 and which == 'ws_num':
                num = num - 2
                if num < 0:
                    num = 0

            if num > 0:
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


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='поставщик')
    quantity = models.FloatField('кол-во', default=0)
    correction = models.FloatField('коррекция', default=0)
    reason = models.CharField('причина', max_length=100, blank=True)

    class Meta:
        verbose_name = 'запас'
        verbose_name_plural = 'запасы'
        unique_together = ('product', 'supplier')


class ProductReview(UserReviewAbstractModel):
    comment = models.TextField('комментарий', max_length=REVIEW_MAX_LENGTH, blank=True)


class Basket(models.Model):
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=30, blank=True)
    utm_source = models.CharField(max_length=20, blank=True)
    secondary = models.BooleanField(default=False)

    def product_cost(self, product):
        if WHOLESALE:
            return product.ws_price - self.product_discount(product)
        else:
            return product.price - self.product_discount(product)

    def product_pct_discount(self, product):
        """ Calculates maximum percent discount based on product, user and maximum discount """
        if WHOLESALE:
            pd = max(product.ws_pct_discount, self.user_discount)
            if pd > product.ws_max_discount:
                pd = product.ws_max_discount
            pdp = round(product.ws_price * Decimal((100 - pd) / 100))
            if pdp < product.sp_price:
                d = product.ws_price - product.sp_price
                pd = int(d / product.ws_price * 100)
        else:
            pd = max(product.pct_discount, self.user_discount)
            if pd > product.max_discount:
                pd = product.max_discount
        return pd

    def product_discount(self, product):
        pd = Decimal(0)
        pct = self.product_pct_discount(product)
        if pct > 0:
            if WHOLESALE:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
        if not WHOLESALE and product.val_discount > pd:
            pd = product.val_discount
        return pd

    def product_discount_text(self, product):
        """ Provides human readable discount string. """
        pd = Decimal(0)
        pdv = 0
        pdt = False
        pct = self.product_pct_discount(product)
        if pct > 0:
            if WHOLESALE:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            pdv = pct
            pdt = True
        if not WHOLESALE and product.val_discount > pd:
            pd = product.val_discount
            pdv = product.val_discount
            pdt = False
        if pd == 0:
            return ''
        pds = ' руб.'
        if pdt:
            pds = '%'
        return '%d%s' % (pdv, pds)

    @property
    def total(self):
        total = Decimal('0')
        for item in self.items.all():
            total += item.price
        return total

    @property
    def quantity(self):
        quantity = 0
        for item in self.items.all():
            quantity += item.quantity
        return quantity

    @cached_property
    def user_discount(self):
        # if session contains valid user, get his discount
        session_data = self.session.get_decoded()
        discount = session_data.get('discount', 0)
        uid = session_data.get('_auth_user_id')
        try:
            user = ShopUser.objects.get(id=uid)
            if user.discount > discount:
                return user.discount
        except ShopUser.DoesNotExist:
            pass
        # if no user data available return session discount
        if not self.phone:
            return discount
        norm_phone = ShopUserManager.normalize_phone(self.phone)
        # if there is a user with such phone get his discount
        try:
            user = ShopUser.objects.get(phone=norm_phone)
            if user.discount > discount:
                return user.discount
        except ShopUser.DoesNotExist:
            pass
        return discount

    def update_session(self, session_key):
        if self.session_id != session_key:
            self.session_id = session_key
            self.save()

    def was_created_recently(self):
        return self.created >= timezone.now() - datetime.timedelta(days=1)
    was_created_recently.admin_order_field = 'created'
    was_created_recently.boolean = True
    was_created_recently.short_description = 'Created recently?'


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, related_name='items', related_query_name='item', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='+', on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    ext_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def price(self):
        if WHOLESALE:
            return (self.cost * Decimal(self.quantity)).quantize(Decimal('0.01'), rounding=ROUND_UP)
        else:
            return (self.cost * Decimal(self.quantity))  # .quantize(Decimal('1'), rounding=ROUND_UP)

    @property
    def cost(self):
        if WHOLESALE:
            return self.product.ws_price - self.discount
        else:
            return (self.product.price - self.discount).quantize(Decimal('1'), rounding=ROUND_UP)

    @property
    def discount(self):
        return self.basket.product_discount(self.product)

    @property
    def discount_text(self):
        """ Provides human readable discount string. """
        return self.basket.product_discount_text(self.product)
