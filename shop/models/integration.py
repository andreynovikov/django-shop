from django.contrib.sites.models import Site
from django.db import models

from . import Product, Supplier, Contractor

__all__ = [
    'Integration', 'ProductIntegration', 'IntegrationCheck'
]


class Integration(models.Model):
    """
    A sales channel, such as a marketplace or a site that takes the product feed, keyed by the storefront it is
    attached to (target_site) and its utm_source. source_site is the channel's own site: its prices go into the feed,
    and orders of an integration that uses the API are placed on it.
    """
    name = models.CharField('название', max_length=100)
    utm_source = models.CharField('источник', max_length=20)
    source_site = models.ForeignKey(Site, verbose_name='сайт-источник', related_name='source_integrations',
                                    related_query_name='source_integration', on_delete=models.PROTECT)
    target_site = models.ForeignKey(Site, verbose_name='сайт-витрина', related_name='integrations',
                                    related_query_name='integration', on_delete=models.PROTECT)
    enabled = models.BooleanField('включена', default=False)
    # The output_ fields shape the channel's product feed: the storefront renders /xml/<utm_source>.xml with the EJS
    # template named here, none without one, from the products that IntegrationViewSet.products() selects
    output_template = models.CharField('шаблон выгрузки', max_length=20, blank=True)
    output_all = models.BooleanField('выгражать все', default=False, help_text="Выгружать товары по дереву категорий, а не по флагу интеграции")
    output_paged = models.BooleanField('выгражать постранично', default=False)
    output_available = models.BooleanField('выгражать только в наличии', default=False)
    output_with_images = models.BooleanField('выгражать только с картинками', default=False)
    output_stock = models.BooleanField('выгражать остатки', default=False)
    output_skip_categories = models.BooleanField('не выгражать категории', default=False)
    # The channel places and tracks its orders through its own API (beru, ozon, wb...): staff can't add, remove or
    # change the quantities of their items, and the orders send nothing to customers
    uses_api = models.BooleanField('использует API', default=False)
    uses_boxes = models.BooleanField('использует коробки', default=False)
    settings = models.JSONField('настройки', null=True, blank=True)
    # Order fields that the admin shows in the buyer's section of the channel's orders
    admin_user_fields = models.JSONField('поля покупателя', null=True, blank=True)
    seller = models.ForeignKey(Contractor, verbose_name='продавец 1С по-умолчанию', related_name='+', blank=True, null=True, on_delete=models.SET_NULL)
    buyer = models.ForeignKey(Contractor, verbose_name='покупатель 1С по-умолчанию', related_name='+', blank=True, null=True, on_delete=models.SET_NULL)
    wirehouse = models.ForeignKey(Supplier, verbose_name='склад отгрузки по-умолчанию', related_name='+', blank=True, null=True,
                                  on_delete=models.SET_NULL, limit_choices_to={'show_in_list': True})
    suppliers = models.ManyToManyField(Supplier, verbose_name='поставщики', related_name='integrations', related_query_name='integration', blank=True)
    products = models.ManyToManyField(Product, related_name='integrations', related_query_name='integration', through='ProductIntegration', blank=True)

    class Meta:
        verbose_name = 'интеграция'
        verbose_name_plural = 'интеграции'
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['target_site', 'utm_source'], name='shop_integration_target_utm_unique')]

    def __str__(self):
        return self.name

    @classmethod
    def get_for_utm_source(cls, utm_source, target_site_id=None):
        if target_site_id is None:
            target_site_id = Site.objects.get_current().pk
        return cls.objects.get(utm_source=utm_source, target_site_id=target_site_id)


class ProductIntegration(models.Model):
    """
    A product in the channel's feed (unless it outputs all products), at its price there. notify_stock is set when
    the product's stock is reset, so that the next run tells the marketplace its new stock.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    price = models.DecimalField('цена, руб', max_digits=10, decimal_places=2, default=0)
    notify_stock = models.BooleanField('требуется уведомление остатков', default=False)
    meta = models.JSONField(null=True, blank=True, editable=False)

    class Meta:
        unique_together = ('product', 'integration')


class IntegrationCheck(models.Model):
    """
    The health of one operation of an integration, such as polling its orders, kept by shop/integration_health.py.
    failures counts the failed attempts since the last success, raised_at is set when they became a problem that the
    managers were told about. Both clear on the next success.
    """
    integration = models.ForeignKey(Integration, verbose_name='интеграция', related_name='checks', on_delete=models.CASCADE)
    # A Celery task name, or a check of its own, such as integration_health.TOKEN
    operation = models.CharField('операция', max_length=100)
    failures = models.PositiveIntegerField('сбоев подряд', default=0)
    error = models.TextField('ошибка', blank=True)
    created_at = models.DateTimeField('создана', auto_now_add=True)
    first_failed_at = models.DateTimeField('первый сбой', null=True, blank=True)
    last_failed_at = models.DateTimeField('последний сбой', null=True, blank=True)
    last_success_at = models.DateTimeField('последний успех', null=True, blank=True)
    raised_at = models.DateTimeField('проблема с', null=True, blank=True)

    class Meta:
        verbose_name = 'состояние интеграции'
        verbose_name_plural = 'состояние интеграций'
        ordering = ['integration__name', 'operation']
        constraints = [models.UniqueConstraint(fields=['integration', 'operation'], name='shop_integrationcheck_unique')]

    def __str__(self):
        from shop.integration_health import label
        return f'{self.integration}: {label(self.operation)}'
