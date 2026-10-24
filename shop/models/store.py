from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse

from . import City, Supplier

__all__ = ['Store', 'StoreImage']


class Store(models.Model):
    city = models.ForeignKey(City, verbose_name='город', on_delete=models.PROTECT)
    site = models.ForeignKey(Site, verbose_name='сайт', on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, verbose_name='склад', related_name='stores', blank=True, null=True, on_delete=models.SET_NULL)
    address = models.CharField('адрес', max_length=255)
    phone = models.CharField('телефон', max_length=100, blank=True)
    name = models.CharField('название', max_length=100)
    pickuponly = models.BooleanField('только ПВЗ', default=False)
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
