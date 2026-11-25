from django.contrib.postgres.fields import ArrayField
from django.contrib.sites.models import Site
from django.db import models

from shop.models import Category, City


class SiteProfile(models.Model):
    """ Shop settings of a django.contrib.sites Site; API views get the site as request.site """
    site = models.OneToOneField(Site, related_name='profile', on_delete=models.CASCADE)
    title = models.CharField('название', max_length=255, blank=True)
    description = models.CharField('описание', max_length=255, blank=True)
    wholesale = models.BooleanField('оптовый', default=False)
    root_category = models.ForeignKey(Category, verbose_name='корневая категория', related_name='profile', null=True, blank=True, on_delete=models.PROTECT)
    # The secret that shop/revalidation.py sends to the storefront's /api/revalidate; sites without one aren't told
    revalidation_token = models.CharField('Токен перегенерации', max_length=30, blank=True)
    # NULL when empty, so that sites without a storefront don't collide on unique
    frontend_key = models.CharField('ключ фронтенда', max_length=64, unique=True, null=True, blank=True,
                                    help_text='Фронтенд сайта отправляет его в заголовке X-Frontend-Key, без ключа API не видит сессий и не принимает изменения без токена.')
    city = models.ForeignKey(City, verbose_name='город', blank=True, null=True, on_delete=models.PROTECT)
    phone = models.CharField('телефон', max_length=255, blank=True, help_text='Указывается на сайте для связи')
    manager_emails = models.CharField('адреса менеджеров', max_length=255, blank=True, help_text='Можно несколько через запятую')
    manager_phones = models.CharField('телефоны менеджеров', max_length=255, blank=True, help_text='Можно несколько через запятую')
    # Goes before the number in an order's title, see Order.title
    order_prefix = models.CharField('префикс заказов', max_length=10, blank=True)
    # The site's own YooKassa shop; without it payments go to the order seller's, see yandex_kassa.configure_yookassa()
    yookassa_id = models.CharField('ID аккаунта ЮKassa', max_length=20, blank=True)
    yookassa_key = models.CharField('секретный ключ ЮKassa', max_length=255, blank=True)
    # Other domains of the site, which SiteDetectionMiddleware takes for it in Origin and Referer
    aliases = ArrayField(models.CharField(max_length=100), verbose_name='домены-ссылки', blank=True, null=True)

    class Meta:
        verbose_name = 'профиль сайта'
        verbose_name_plural = 'профили сайтов'

    def __str__(self):
        return self.title or self.site.name
