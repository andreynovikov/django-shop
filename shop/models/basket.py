import datetime

from decimal import Decimal, ROUND_UP, ROUND_HALF_EVEN

from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.sessions.models import Session
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from . import Product, ShopUser, ShopUserManager

__all__ = [
    'Basket', 'BasketItem', 'Favorites'
]


class Basket(models.Model):
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=30, blank=True)
    utm_source = models.CharField(max_length=20, blank=True)
    secondary = models.BooleanField(default=False)

    def product_cost(self, product):
        if self.site.profile.wholesale:
            return product.ws_price - self.product_discount(product)
        else:
            return product.price - self.product_discount(product)

    @classmethod
    def product_cost_for_user(cls, wholesale, product, user):
        if wholesale:
            return product.ws_price - cls.product_discount_with_user_discount(wholesale, product, user.discount)
        else:
            return product.price - cls.product_discount_with_user_discount(wholesale, product, user.discount)

    @classmethod
    def product_pct_discount(cls, wholesale, product, user_discount):
        """ Calculates maximum percent discount based on product, user discount and maximum allowed discount """
        if wholesale:
            pd = max(product.ws_pct_discount, user_discount)
            if pd > product.ws_max_discount:
                pd = product.ws_max_discount
            pdp = round(product.ws_price * Decimal((100 - pd) / 100))
            if pdp < product.sp_price:
                d = product.ws_price - product.sp_price
                pd = int(d / product.ws_price * 100)
        else:
            pd = max(product.pct_discount, user_discount)
            if pd > product.max_discount:
                pd = product.max_discount
        return pd

    @classmethod
    def product_discount_with_user_discount(cls, wholesale, product, user_discount):
        """ Calculates final product discount considering user discount """
        pd = Decimal(0)
        pct = cls.product_pct_discount(wholesale, product, user_discount)
        if pct > 0:
            if wholesale:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
        if not wholesale and product.val_discount > pd:
            pd = product.val_discount
        return pd

    def product_discount(self, product):
        """ Provides discount for basket items using basket owner """
        return self.product_discount_with_user_discount(self.site.profile.wholesale, product, self.user_discount)

    def product_discount_text(self, product):
        """ Provides human readable discount string. """
        pd = Decimal(0)
        pdv = Decimal(0)
        pdt = False
        pct = self.product_pct_discount(self.site.profile.wholesale, product, self.user_discount)
        if pct > 0:
            if self.site.profile.wholesale:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            pdv = Decimal(pct)
            pdt = True
        if not self.site.profile.wholesale and product.val_discount > pd:
            pd = product.val_discount
            pdv = product.val_discount
            pdt = False
        if pd == 0:
            return ''
        pds = ' руб.'
        if pdt:
            pds = '%'
        return '{}{}'.format(intcomma(pdv.quantize(Decimal('1'), rounding=ROUND_UP)), pds)

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
    meta = models.JSONField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ['id']

    @property
    def price(self):
        if self.basket.site.profile.wholesale:
            return (self.cost * Decimal(self.quantity)).quantize(Decimal('0.01'), rounding=ROUND_UP)
        else:
            return (self.cost * Decimal(self.quantity))  # .quantize(Decimal('1'), rounding=ROUND_UP)

    @property
    def cost(self):
        if self.basket.site.profile.wholesale:
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


class Favorites(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранные'
        unique_together = ('product', 'user')
        ordering = ['id']
