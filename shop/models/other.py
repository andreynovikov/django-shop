import logging

from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone
from django.urls import reverse

from mptt.models import MPTTModel, TreeForeignKey

__all__ = [
    'Category', 'Currency', 'Country', 'Region', 'City',
    'Contractor', 'PosTerminal', 'Supplier', 'Store', 'StoreImage', 'ServiceCenter',
    'Manufacturer', 'Advert', 'SalesAction', 'News'
]

logger = logging.getLogger(__name__)


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.PROTECT)
    active = models.BooleanField('включена', default=True, db_index=True)
    hidden = models.BooleanField('спрятана', default=False, db_index=True)
    feed = models.BooleanField('выдавать в фиды', default=True)
    filters = models.CharField('фильтры', max_length=255, blank=True)
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    svg_icon = models.TextField('SVG иконка', blank=True)
    image = models.ImageField('изображение', upload_to='categories', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    promo_image = models.ImageField('промо изображение', upload_to='categories', blank=True,
                                    width_field='promo_image_width', height_field='promo_image_height')
    promo_image_width = models.IntegerField(null=True, blank=True)
    promo_image_height = models.IntegerField(null=True, blank=True)
    product_order = models.CharField('поле сортировки товаров', max_length=50, default='-price')

    def get_api_path(self):
        # TODO: refactor: remove mptt_urls get_path injection, use this instead
        return '/'.join([item.slug for item in self.get_ancestors(include_self=True)[1:]])  # exclude root category

    def get_active_children(self):
        return self.get_children().filter(active=True, hidden=False)

    def get_active_descendants(self):
        return self.get_descendants().filter(active=True, hidden=False)

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


class Contractor(models.Model):
    # numerical values taken from https://yookassa.ru/developers/payment-acceptance/receipts/54fz/other-services/parameters-values
    TAX_SYSTEM_GTS = 1
    TAX_SYSTEM_STS = 2
    TAX_SYSTEM_CHOICES = (
        (TAX_SYSTEM_GTS, 'ОСН'),
        (TAX_SYSTEM_STS, 'УСН'),
    )
    VAT_RATE_NONE = 1
    VAT_RATE_ZERO = 2
    VAT_RATE_TEN = 3
    VAT_RATE_RECEIPT_TWENTY = 4
    VAT_RATE_FIVE = 7
    VAT_RATE_SEVEN = 8
    VAT_RATE_CHOICES = (
        (VAT_RATE_NONE, 'Без НДС'),
        (VAT_RATE_ZERO, 'НДС по ставке 0%'),
        (VAT_RATE_FIVE, 'НДС по ставке 5%'),
        (VAT_RATE_SEVEN, 'НДС по ставке 7%'),
        (VAT_RATE_TEN, 'НДС по ставке 10%'),
        (VAT_RATE_RECEIPT_TWENTY, 'НДС чека по ставке 20%'),
    )
    code = models.CharField('код 1С', max_length=64)
    name = models.CharField('название', max_length=100)
    is_seller = models.BooleanField('продавец', default=False)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    ogrn = models.CharField('ОГРН', max_length=13, blank=True)
    tax_system = models.SmallIntegerField('система налогообложения', choices=TAX_SYSTEM_CHOICES, blank=True, null=True)
    vat_rate = models.SmallIntegerField('ставка НДС', choices=VAT_RATE_CHOICES, blank=True, null=True)
    legal_address = models.TextField('юр. адрес', blank=True)
    postal_address = models.TextField('физ. адрес', blank=True)
    bank_requisites = models.TextField('банковские реквизиты', blank=True)
    stamp = models.ImageField('печать', upload_to='contractors', blank=True)
    script = models.ImageField('подпись', upload_to='contractors', blank=True)
    yookassa_id = models.CharField('ID аккаунта ЮKassa', max_length=20, blank=True)
    yookassa_key = models.CharField('секретный ключ ЮKassa', max_length=255, blank=True)
    modulkassa_login = models.CharField('логин МодульКасса', max_length=255, blank=True)
    modulkassa_password = models.CharField('пароль МодульКасса', max_length=255, blank=True)

    class Meta:
        verbose_name = 'контрагент'
        verbose_name_plural = 'контрагенты'

    def __str__(self):
        return self.name


class PosTerminal(models.Model):
    id = models.CharField('идентификатор кассы', max_length=100, primary_key=True)
    seller = models.ForeignKey(Contractor, verbose_name='продавец', on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'pos-терминал'
        verbose_name_plural = 'pos-терминалы'

    def __str__(self):
        return self.id


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
    show_in_list = models.BooleanField('показывать в списках', default=False, db_index=True)
    count_in_stock = models.SmallIntegerField('учитывать в наличии', choices=COUNT_CHOICES, default=COUNT_NONE)
    express_count_in_stock = models.SmallIntegerField('учитывать в наличии Экспресс', choices=COUNT_CHOICES, default=COUNT_NONE)
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
    publish = models.BooleanField('публиковать в картах', default=True)
    marketplace = models.BooleanField('участник акции с маркетплейсами', default=False)
    lottery = models.BooleanField('участник лотереи', default=False)
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

    def phones_as_list(self):
        return filter(lambda x: x, [self.phone] + [x.strip() for x in self.phone2.split(',')])

    def hours_as_list(self):
        return [x.strip() for x in self.hours.split(',')]

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains', 'address__icontains', 'city__name__icontains']

    def get_absolute_url(self):
        return reverse('store', args=[str(self.pk)])

    def __str__(self):
        return str(self.city) + ', ' + self.address


class StoreImage(models.Model):
    KIND_EXTERIOR = 'exterior'
    KIND_INTERIOR = 'interior'
    KIND_ENTRANCE = 'enter'
    KIND_LOGO = 'logo'
    KIND_GOODS = 'goods'
    KIND_FOOD = 'food'
    IMAGE_KINDS = (
        (KIND_EXTERIOR, 'экстерьер'),
        (KIND_INTERIOR, 'интерьер'),
        (KIND_ENTRANCE, 'вход'),
        (KIND_LOGO, 'логотип'),
        (KIND_GOODS, 'товары'),
        (KIND_FOOD, 'блюда, напитки')
    )
    store = models.ForeignKey(Store, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('изображение', upload_to='stores', width_field='image_width', height_field='image_height')
    image_width = models.IntegerField()
    image_height = models.IntegerField()
    kind = models.CharField('тип', max_length=50, choices=IMAGE_KINDS, default=KIND_EXTERIOR)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'изображение магазина'
        verbose_name_plural = 'изображения магазина'
        ordering = ['order']


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

    def phones_as_list(self):
        return [x.strip() for x in self.phone.split(',')]

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


class News(models.Model):
    title = models.CharField('заголовок', max_length=255)
    image = models.ImageField('изображение', upload_to='news', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    content = models.TextField('содержимое')
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    active = models.BooleanField('активная', db_index=True)
    publish_date = models.DateTimeField('дата публикации', default=timezone.now)

    class Meta:
        verbose_name = 'новость'
        verbose_name_plural = 'новости'
        ordering = ['-publish_date']

    def __str__(self):
        return self.title
