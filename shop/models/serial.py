from django.db import IntegrityError, models

from celery import current_app

from . import Product, Order, OrderItem, ShopUser

__all__ = [
    'Serial'
]


class Serial(models.Model):
    number = models.CharField('SN', max_length=30, unique=True)
    user = models.ForeignKey(ShopUser, verbose_name='пользователь', related_name='serials', on_delete=models.PROTECT)
    purchase_date = models.DateField('дата покупки', blank=True, null=True)
    product = models.ForeignKey(Product, related_name='+', verbose_name='товар', blank=True, null=True, on_delete=models.PROTECT)
    order = models.ForeignKey(Order, related_name='serials', verbose_name='заказ', blank=True, null=True, on_delete=models.PROTECT)
    approved = models.BooleanField('проверен', default=False)
    comment = models.TextField('комментарий менеджера', blank=True)

    class Meta:
        verbose_name = 'гарантийный талон'
        verbose_name_plural = 'гарантийные талоны'
        ordering = ['-purchase_date', 'number']

    def __str__(self):
        return self.number

    @classmethod
    def register(cls, sn, user):
        item = OrderItem.objects.filter(serial_number__iexact=sn).order_by('-order').first()
        if item is not None:
            if item.order.user == user:
                # Вариант 1: пользователь зарегистрирован и покупал товар с таким номером
                serial = Serial(
                    number=sn,
                    user=user,
                    product=item.product,
                    order=item.order,
                    purchase_date=item.order.created,
                    approved=True
                )

            elif 'FBO' in item.order.name:  # TODO: find proper way to identify such orders
                # Вариант 2: товар с таким номером отгружался по FBO
                order = Order(
                    site=item.order.site,
                    user=user,
                    name=user.name,
                    phone=user.phone,
                    created=item.order.created,
                    status=Order.STATUS_DONE,
                    manager_comment='Заказ сформирован при регистрации гарантийного талона из заказа №{}'.format(item.order.pk)
                )
                order.save()
                order.items.create(
                    product=item.product,
                    product_price=item.product_price,
                    serial_number=sn,
                    quantity=1
                )
                update = {}
                message = 'Товар с серийным номером {} перенесён в заказ №{}'.format(sn, order.pk)
                if item.order.manager_comment:
                    update['manager_comment'] = '\n'.join([item.order.manager_comment, message])
                else:
                    update['manager_comment'] = message
                # call task by name to prevent circular model import
                current_app.send_task('shop.tasks.update_order', (item.order.pk, update))

                serial = Serial(
                    number=sn,
                    user=user,
                    product=item.product,
                    order=order,
                    approved=True
                )

            else:
                # Вариант 3: кто-то другой покупал товар с таким номером
                serial = Serial(
                    number=sn,
                    user=user,
                    product=item.product,
                    order=item.order,
                    purchase_date=item.order.created
                )

        else:
            # Вариант 4: о таком номере ничего неизвестно
            serial = Serial(number=sn, user=user)

        try:
            serial.save()
        except IntegrityError:
            return None

        return serial
