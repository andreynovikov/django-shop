import logging

from decimal import Decimal, ROUND_UP, ROUND_DOWN, ROUND_HALF_EVEN

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.functional import cached_property

from model_utils import FieldTracker
from colorfield.fields import ColorField
from tagging.utils import parse_tag_input

from . import Product, ProductSet, Store, ShopUser

__all__ = [
    'Contractor', 'Manager', 'Courier', 'Order', 'OrderItem', 'Box'
]

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)
ORDER_CODES = getattr(settings, 'SHOP_ORDER_CODES', {})


class Contractor(models.Model):
    code = models.CharField('код 1С', max_length=64)
    name = models.CharField('название', max_length=100)

    class Meta:
        verbose_name = 'контрагент'
        verbose_name_plural = 'контрагенты'

    def __str__(self):
        return self.name


class Manager(models.Model):
    name = models.CharField('имя', max_length=100)
    color = ColorField(default='#000000')

    class Meta:
        verbose_name = 'менеджер'
        verbose_name_plural = 'менеджеры'

    def __str__(self):
        return self.name


class Courier(models.Model):
    name = models.CharField('имя', max_length=100)
    color = ColorField(default='#000000')
    pos_id = models.CharField('идентификатор кассы', max_length=100, blank=True)

    class Meta:
        verbose_name = 'курьер'
        verbose_name_plural = 'курьеры'

    def __str__(self):
        return self.name


# may be switch to https://github.com/5monkeys/django-enumfield/
class Order(models.Model):
    PAYMENT_CASH = 1
    PAYMENT_CARD = 2
    PAYMENT_TRANSFER = 3
    PAYMENT_COD = 4
    PAYMENT_POS = 5
    PAYMENT_CREDIT = 6
    PAYMENT_UNKNOWN = 99
    PAYMENT_CHOICES = (
        (PAYMENT_UNKNOWN, 'уточняется'),
        (PAYMENT_CASH, 'наличные'),
        (PAYMENT_CARD, 'банковская карта'),
        (PAYMENT_TRANSFER, 'банковский перевод'),
        (PAYMENT_COD, 'наложенный платёж'),
        (PAYMENT_POS, 'платёжный терминал'),
        (PAYMENT_CREDIT, 'кредит'),
    )
    DELIVERY_COURIER = 1
    DELIVERY_CONSULTANT = 2
    DELIVERY_SELF = 3
    DELIVERY_TRANSPORT = 4
    DELIVERY_PICKPOINT = 5
    DELIVERY_YANDEX = 6
    DELIVERY_TRANSIT = 7
    DELIVERY_UNKNOWN = 99
    DELIVERY_CHOICES = (
        (DELIVERY_UNKNOWN, 'уточняется'),
        (DELIVERY_COURIER, 'курьер'),
        (DELIVERY_CONSULTANT, 'консультант'),
        (DELIVERY_SELF, 'получу сам в магазине'),
        (DELIVERY_TRANSPORT, 'транспортная компания'),
        (DELIVERY_PICKPOINT, 'PickPoint'),
        (DELIVERY_YANDEX, 'Яндекс.Доставка'),
        (DELIVERY_TRANSIT, 'транзит'),
    )
    STATUS_NEW = 0x0
    STATUS_ACCEPTED = 0x00000001
    STATUS_COLLECTING = 0x00000004
    STATUS_CANCELED = 0x00000008
    STATUS_FROZEN = 0x00000010
    STATUS_OTHERSHOP = 0x00000020
    STATUS_COLLECTED = 0x00000040
    STATUS_SERVICE = 0x00000080
    STATUS_DELIVERED_SHOP = 0x00000100
    STATUS_DELIVERED_STORE = 0x00000200
    STATUS_SENT = 0x00000400
    STATUS_DELIVERED = 0x00000800
    STATUS_CONSULTATION = 0x00001000
    STATUS_PROBLEM = 0x00002000
    STATUS_DONE = 0x00004000
    STATUS_RETURNING = 0x02000000
    STATUS_UNCLAIMED = 0x04000000
    STATUS_FINISHED = 0x0F000000
    STATUS_CHOICES = (
        (STATUS_NEW, 'новый заказ'),
        (STATUS_ACCEPTED, 'принят в работу'),
        (STATUS_COLLECTING, 'комплектуется'),
        (STATUS_CANCELED, 'отменен'),
        (STATUS_FROZEN, 'заморожен'),
        (STATUS_OTHERSHOP, 'передан в другой магазин'),
        (STATUS_COLLECTED, 'собран'),
        (STATUS_SERVICE, 'сервис'),
        (STATUS_SENT, 'доставляется'),
        (STATUS_DELIVERED, 'доставлен'),
        (STATUS_DELIVERED_SHOP, 'доставлен в магазин'),
        (STATUS_DELIVERED_STORE, 'передан в службу доставки'),
        (STATUS_CONSULTATION, 'консультация'),
        (STATUS_PROBLEM, 'проблема'),
        (STATUS_RETURNING, 'возвращается'),
        (STATUS_UNCLAIMED, 'не востребован'),
        (STATUS_DONE, 'завершён'),
        (STATUS_FINISHED, 'выполнен'),
    )
    STATUS_COLORS = {
        STATUS_NEW: 'red',
        STATUS_ACCEPTED: 'orange',
        STATUS_COLLECTING: 'limegreen',
        STATUS_CANCELED: 'pink',
        STATUS_FROZEN: 'lightblue',
        STATUS_OTHERSHOP: 'gray',
        STATUS_COLLECTED: 'orange',
        STATUS_SERVICE: 'blue',
        STATUS_SENT: 'gray',
        STATUS_DELIVERED: 'darkgreen',
        STATUS_DELIVERED_SHOP: 'gray',
        STATUS_DELIVERED_STORE: 'gray',
        STATUS_CONSULTATION: 'darkgreen',
        STATUS_PROBLEM: 'black',
        STATUS_RETURNING: 'blue',
        STATUS_UNCLAIMED: 'black',
        STATUS_DONE: 'gray',
        STATUS_FINISHED: 'gray',
    }
    PICKPOINT_SERVICE_STD = 'STD'
    PICKPOINT_SERVICE_STDCOD = 'STDCOD'
    PICKPOINT_SERVICES = (
        (PICKPOINT_SERVICE_STD, 'предоплаченный товар'),
        (PICKPOINT_SERVICE_STDCOD, 'наложенный платеж'),
    )
    PICKPOINT_RECEPTION_CUR = 'CUR'
    PICKPOINT_RECEPTION_WIN = 'WIN'
    PICKPOINT_RECEPTIONS = (
        (PICKPOINT_RECEPTION_CUR, 'вызов курьера'),
        (PICKPOINT_RECEPTION_WIN, 'самопривоз'),
    )
    # order
    comment = models.TextField('комментарий', blank=True)
    shop_name = models.CharField('магазин', max_length=20, blank=True)
    site = models.ForeignKey(Site, verbose_name='сайт', on_delete=models.PROTECT)
    payment = models.SmallIntegerField('оплата', choices=PAYMENT_CHOICES, default=PAYMENT_UNKNOWN)
    paid = models.BooleanField('оплачен', default=False)
    manager = models.ForeignKey(Manager, verbose_name='менеджер', blank=True, null=True, on_delete=models.SET_NULL)
    manager_comment = models.TextField('комментарий менеджера', blank=True)
    alert = models.CharField('тревога', max_length=255, blank=True, db_index=True)
    meta = JSONField(null=True, blank=True, editable=False)
    # delivery
    delivery = models.SmallIntegerField('доставка', choices=DELIVERY_CHOICES, default=DELIVERY_UNKNOWN, db_index=True)
    delivery_price = models.DecimalField('стоимость доставки', max_digits=8, decimal_places=2, default=0)
    delivery_info = models.TextField('ТК, ТТН, курьер', blank=True)
    delivery_tracking_number = models.CharField('трек-код', max_length=30, blank=True, db_index=True)
    delivery_dispatch_date = models.DateField('дата отправки', blank=True, null=True)
    delivery_handing_date = models.DateField('дата получения', blank=True, null=True)
    delivery_time_from = models.TimeField('от', blank=True, null=True)
    delivery_time_till = models.TimeField('до', blank=True, null=True)
    delivery_size_length = models.PositiveSmallIntegerField('длина', default=0)
    delivery_size_width = models.PositiveSmallIntegerField('ширина', default=0)
    delivery_size_height = models.PositiveSmallIntegerField('высота', default=0)
    delivery_yd_order = models.CharField('ЯД заказ', max_length=20, blank=True)
    delivery_pickpoint_terminal = models.CharField('терминал', max_length=10, blank=True)
    delivery_pickpoint_service = models.CharField('тип сдачи', max_length=10, choices=PICKPOINT_SERVICES, default=PICKPOINT_SERVICE_STD)
    delivery_pickpoint_reception = models.CharField('вид приема', max_length=10, choices=PICKPOINT_RECEPTIONS, default=PICKPOINT_RECEPTION_CUR)
    buyer = models.ForeignKey(Contractor, verbose_name='покупатель 1С', related_name='покупатель', blank=True, null=True, on_delete=models.SET_NULL)
    seller = models.ForeignKey(Contractor, verbose_name='продавец 1С', related_name='продавец', blank=True, null=True, on_delete=models.SET_NULL)
    wiring_date = models.DateField('дата проводки', blank=True, null=True)
    courier = models.ForeignKey(Courier, verbose_name='курьер', blank=True, null=True, on_delete=models.SET_NULL)
    store = models.ForeignKey(Store, verbose_name='магазин самовывоза', blank=True, null=True, on_delete=models.PROTECT)
    utm_source = models.CharField(max_length=20, blank=True)
    # user
    user = models.ForeignKey(ShopUser, verbose_name='покупатель', related_name='orders', on_delete=models.PROTECT)
    name = models.CharField('имя', max_length=100, blank=True)
    postcode = models.CharField('индекс', max_length=10, blank=True)
    city = models.CharField('город', max_length=255, blank=True)
    address = models.CharField('адрес', max_length=255, blank=True)
    phone = models.CharField('телефон', max_length=30, blank=True)
    phone_aux = models.CharField('доп.телефон', max_length=30, blank=True)
    email = models.EmailField('эл.почта', blank=True)
    is_firm = models.BooleanField('юр.лицо', default=False)
    firm_name = models.CharField('название организации', max_length=255, blank=True)
    firm_address = models.CharField('Юр.адрес', max_length=255, blank=True)
    firm_details = models.TextField('реквизиты', blank=True)
    # state
    created = models.DateTimeField('создан', auto_now_add=True)
    status = models.PositiveIntegerField('статус', choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    hidden_tracking_number = models.CharField(max_length=50, blank=True, db_index=True)

    tracker = FieldTracker(fields=['status'])

    @property
    def title(self):
        shop_code = ORDER_CODES.get(self.site.domain, '?')
        if shop_code:
            shop_code = shop_code + '-'
        return '{}{}'.format(shop_code, self.id)

    @property
    def total(self):
        return self.products_price + self.delivery_price

    @property
    def products_price(self):
        total = 0
        for item in self.items.all():
            total += item.price
        return total

    @property
    def products_quantity(self):
        quantity = 0
        for item in self.items.all():
            quantity += item.quantity
        return quantity

    @property
    def weight(self):
        weight = 0
        for box in self.boxes.all():
            if box.weight == 0:
                return None
            weight += box.weight
        if weight > 0:
            return weight
        for item in self.items.all():
            if item.product.prom_weight == 0:
                return None
            weight += item.product.prom_weight
        return weight

    @cached_property
    def is_beru(self):
        return self.site in (
            Site.objects.get(domain='beru.ru'),
            Site.objects.get(domain='taxi.beru.ru'),
            Site.objects.get(domain='tax2.beru.ru')
        )

    @cached_property
    def is_from_market(self):
        return self.site == Site.objects.get(domain='market.yandex.ru')

    @staticmethod
    def register(basket):
        session_data = basket.session.get_decoded()
        uid = session_data.get('_auth_user_id')
        user = ShopUser.objects.get(id=uid)
        if basket.utm_source == 'yamarket':
            site = Site.objects.get(domain='market.yandex.ru')
        elif basket.utm_source == 'beru':
            site = Site.objects.get(domain='beru.ru')
        elif basket.utm_source == 'taxi':
            site = Site.objects.get(domain='taxi.beru.ru')
        elif basket.utm_source == 'tax2':
            site = Site.objects.get(domain='tax2.beru.ru')
        elif basket.utm_source == 'sber':
            site = Site.objects.get(domain='sbermegamarket.ru')
        else:
            site = Site.objects.get_current()
        order = Order.objects.create(user=user, site=site)
        order.utm_source = basket.utm_source
        order.name = user.name
        order.postcode = user.postcode
        order.city = user.city
        order.address = user.address
        order.phone = user.phone
        order.email = user.email

        if WHOLESALE:
            qnt = Decimal('0.01')
        else:
            qnt = Decimal('1')

        # добавляем в заказ все элементы корзины
        for item in basket.items.all():
            # если это Беру, то указываем только рублёвую скидку, предоставленную Беру
            if order.utm_source in ('beru', 'taxi', 'tax2'):
                pct_discount = 0
                val_discount = item.ext_discount
                price = item.product.price
            # если это опт, то указываем только рублёвую скидку, высчитанную корзиной
            elif WHOLESALE:
                pct_discount = 0
                val_discount = item.discount
                price = item.product.ws_price
            # иначе считаем отдельно скидку в процентах и копируем текущую рублёвую скидку товара
            else:
                pct_discount = basket.product_pct_discount(item.product)
                val_discount = item.product.val_discount
                price = item.product.price
            # если это обычный товар, добавляем его в заказ
            if item.product.constituents.count() == 0:
                order.items.create(product=item.product,
                                   product_price=price.quantize(qnt, rounding=ROUND_UP),
                                   pct_discount=pct_discount,
                                   val_discount=val_discount,
                                   quantity=item.quantity,
                                   meta=item.meta)
            # если это комплект, то добавляем элементы комплекта отдельно
            else:
                full_discount = val_discount
                discount_remainder = full_discount
                if not item.product.recalculate_price:
                    if WHOLESALE:
                        full_price = item.product.ws_price
                    else:
                        full_price = item.product.price
                    full_price = full_price.quantize(qnt, rounding=ROUND_UP)
                    price_remainder = full_price
                constituents = ProductSet.objects.filter(declaration=item.product)
                last = len(constituents) - 1
                for idx, itm in enumerate(constituents):
                    if WHOLESALE:
                        constituent_price = itm.constituent.ws_price
                    else:
                        constituent_price = itm.constituent.price
                    item_price = 0
                    item_total = 0
                    proportion = Decimal(itm.constituent.price / item.product.price)
                    # если комплект динамически пересчитывает цену, то указываем цену элемента
                    if item.product.recalculate_price:
                        item_price = (constituent_price * Decimal((100 - itm.discount) / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
                        if itm.quantity > 1:
                            item_total = item_price * itm.quantity * item.quantity
                    # иначе разбиваем цену комплекта на части пропорционально ценам элементов
                    elif idx < last:
                        item_price = (constituent_price * proportion).quantize(qnt, rounding=ROUND_HALF_EVEN)
                        price_remainder = price_remainder - item_price * itm.quantity
                        if itm.quantity > 1:
                            item_total = item_price * itm.quantity * item.quantity
                    else:
                        item_price = price_remainder / itm.quantity
                        if itm.quantity > 1:
                            item_total = price_remainder * item.quantity
                    # рублёвую скидку в любом случае разбиваем на части пропорционально ценам элементов
                    if idx < last:
                        if itm.quantity > 1:
                            val_discount = (full_discount * proportion * itm.quantity).quantize(qnt, rounding=ROUND_DOWN)
                            discount_remainder = discount_remainder - val_discount
                        else:
                            val_discount = (full_discount * proportion).quantize(qnt, rounding=ROUND_HALF_EVEN)
                            discount_remainder = discount_remainder - val_discount
                    else:
                        val_discount = discount_remainder
                    i = order.items.create(product=itm.constituent,
                                           product_price=item_price,
                                           pct_discount=pct_discount,
                                           val_discount=val_discount,
                                           quantity=item.quantity * itm.quantity,
                                           total=item_total,
                                           meta=item.meta)
                    # в данный момент, если цена позиции равна нулю, то она принудительно устанавливается в цену товара
                    # todo: можно перенести эту логику в admin, и тогда можно будет избавиться от двойного сохранения
                    if not item_price:
                        i.product_price = item_price
                        i.save()
        return order

    def append_user_tags(self, tags):
        user_tags = parse_tag_input(self.user.tags)
        print(user_tags)
        print(tags)
        merged = list(set(tags + user_tags))
        print(merged)
        self.user.tags = ','.join(merged)
        self.user.save()

    def __str__(self):
        return "%s от %s" % (self.id, date_format(timezone.localtime(self.created), "DATETIME_FORMAT"))

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        permissions = (
            ('change_order_spb', "Может редактировать заказы СПб"),
        )


class Box(models.Model):
    order = models.ForeignKey(Order, related_name='boxes', related_query_name='box', on_delete=models.CASCADE)
    weight = models.FloatField('вес, кг', default=0)
    length = models.DecimalField('длина, см', max_digits=5, decimal_places=2, default=0)
    width = models.DecimalField('ширина, см', max_digits=5, decimal_places=2, default=0)
    height = models.DecimalField('высота, см', max_digits=5, decimal_places=2, default=0)

    def num(self, n):
        return int(n) if n == int(n) else n

    @property
    def code(self):
        return "{:010d}".format(self.pk)

    def __str__(self):
        if self.pk:
            return "{:010d} - {}x{}x{}см".format(self.pk, self.num(self.length), self.num(self.width), self.num(self.height))
        else:
            return super(Box, self).__str__()

    class Meta:
        verbose_name = 'коробка'
        verbose_name_plural = 'коробки'
        ordering = ['id']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', related_query_name='item', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='+', verbose_name='товар', on_delete=models.PROTECT)
    product_price = models.DecimalField('цена товара', max_digits=10, decimal_places=2, default=0)
    pct_discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    val_discount = models.DecimalField('скидка, руб', max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveSmallIntegerField('количество', default=1)
    total = models.DecimalField('сумма', max_digits=10, decimal_places=2, default=0)
    serial_number = models.CharField('SN', max_length=30, blank=True)
    box = models.ForeignKey(Box, blank=True, null=True, related_name='products', related_query_name='box', verbose_name='коробка', on_delete=models.SET_NULL)
    meta = JSONField(null=True, blank=True, editable=False)

    @property
    def price(self):
        if self.total > 0:
            price = self.total
            pd = Decimal(0)
            if self.pct_discount > 0:
                if WHOLESALE:
                    qnt = Decimal('0.01')
                else:
                    qnt = Decimal('1')
                pd = (price * Decimal(self.pct_discount / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            if self.val_discount > pd:
                pd = self.val_discount
            return price - pd
        else:
            return (self.product_price - self.discount) * self.quantity

    @property
    def cost(self):
        return self.product_price - self.discount

    @property
    def discount(self):
        pd = Decimal(0)
        if self.pct_discount > 0:
            price = self.product_price
            if WHOLESALE:
                qnt = Decimal('0.01')
            else:
                qnt = Decimal('1')
            pd = (price * Decimal(self.pct_discount / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
        if self.val_discount > pd:
            pd = self.val_discount
        return pd

    @property
    def discount_text(self):
        """ Provides human readable discount string. """
        pd = Decimal(0)
        pdv = 0
        pdt = False
        if self.pct_discount > 0:
            price = self.product_price
            if WHOLESALE:
                qnt = Decimal('0.01')
            else:
                qnt = Decimal('1')
            pd = (price * Decimal(self.pct_discount / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            pdv = self.pct_discount
            pdt = True
        if self.val_discount > pd:
            pd = self.val_discount
            pdv = self.val_discount
            pdt = False
        if pd == 0:
            return ''
        pds = ' руб.'
        if pdt:
            pds = '%'
        return '%d%s' % (pdv, pds)

    def __str__(self):
        return "%s, %d шт." % (self.product.title, self.quantity)

    class Meta:
        verbose_name = 'товарная позиция'
        verbose_name_plural = 'товарные позиции'


def set_order_item_price(sender, instance, **kwargs):
    if instance._state.adding is True:
        if not instance.product_price:
            instance.product_price = instance.product.price


pre_save.connect(set_order_item_price, sender=OrderItem, dispatch_uid="set_order_item_price")
