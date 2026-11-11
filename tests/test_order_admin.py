"""
What staff do with orders in the admin besides the form: supplier spreadsheets, delivery, acts, 1C export,
combining orders and discounts. The views are called directly, see settings.py on how to run.
"""
import datetime
import io
from types import SimpleNamespace
from unittest import mock

import openpyxl

from django import forms
from django.contrib.admin import helpers
from django.contrib.admin.sites import site as admin_site
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path, reverse

from shop.admin.forms import YandexDeliveryForm
from shop.models import Act, ActOrder, Box, Contractor, Order, OrderItem, ShopUser, Stock, Supplier

from .fixtures import add_marketplace_sites, add_product

# The admin is served by a process of its own (ADMIN=True), its views and templates need its URLs
urlpatterns = [path('admin/', admin_site.urls)]

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# Warehouses of Yandex Delivery come from settings of the deployment
WAREHOUSE = forms.ChoiceField(choices=[('w1', 'Склад')])


def sheets(response):
    """ Rows of each sheet of a spreadsheet """
    workbook = openpyxl.load_workbook(io.BytesIO(response.content))
    return {sheet.title: [row for row in sheet.iter_rows(values_only=True)] for sheet in workbook}


class FakeFormset(list):
    """ Inline forms of a formset, as save_related() goes through them """
    def __init__(self, model, forms):
        super().__init__(forms)
        self.empty_form = SimpleNamespace(instance=model())

    def save(self):
        pass


@override_settings(ROOT_URLCONF=__name__)
class Base(TestCase):
    def setUp(self):
        add_marketplace_sites()
        self.site = Site.objects.get_current()
        self.seller = Contractor.objects.create(code='seller', name='ООО Продавец')
        for target, new in (
            # Constance refuses the local-memory cache of the tests
            ('shop.models.order.config', SimpleNamespace(sw_default_seller=self.seller.pk)),
            ('shop.signals.logger', mock.Mock()),  # logs every product put in an order
        ):
            patcher = mock.patch(target, new=new)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.staff = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        self.user = ShopUser.objects.create(phone='+79161234567', name='Покупатель')
        self.admin = admin_site._registry[Order]
        self.machine = add_product(1, article='A1', title='Janome', max_discount=15,
                                   prom_weight=5, length=50, width=40, height=30)
        self.needles = add_product(2, article='A2', title='Иглы', max_discount=10,
                                   prom_weight=0.1, length=10, width=5, height=1)
        self.thread = add_product(3, article='A3', title='Нитки')

    def request(self, data=None, query=None):
        """ POST of the data, or GET with the query """
        request = RequestFactory().post('/', data) if data is not None else RequestFactory().get('/', query)
        request.user = self.staff
        request.user.is_verified = lambda: True  # passed the second factor, as OTPMiddleware tells the admin site
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return request

    def messages(self, request):
        return [str(message) for message in request._messages]

    def order(self, *items, **fields):
        """ An order with (product, quantity) items """
        fields.setdefault('user', self.user)
        fields.setdefault('site', self.site)
        fields.setdefault('seller', self.seller)
        order = Order.objects.create(**fields)
        for product, quantity in items:
            order.items.create(product=product, product_price=1000, quantity=quantity)
        return order

    def selected(self, *orders, **data):
        """ Request of an action on the orders in the list """
        return self.request({helpers.ACTION_CHECKBOX_NAME: [order.pk for order in orders], **data})

    def queryset(self, *orders):
        return Order.objects.filter(pk__in=[order.pk for order in orders])


class SupplyTests(Base):
    def setUp(self):
        super().setUp()
        self.own = Supplier.objects.create(code='Ур', code1c='own', name='Свой склад', order=1, show_in_order=True)
        self.supplier = Supplier.objects.create(code='С3', code1c='s3', name='Поставщик', order=2, show_in_order=True)
        self.aux = Supplier.objects.create(code='Доп', code1c='aux', name='Другой поставщик', order=3)
        for product, supplier, quantity, correction in (
            (self.machine, self.own, 2, -1),
            (self.machine, self.supplier, 1, 0),
            (self.machine, self.aux, 5, 0),
            (self.needles, self.own, 10, 0),
            (self.thread, self.own, 0, 0),
            (self.thread, self.supplier, 2, 0),
        ):
            Stock.objects.create(product=product, supplier=supplier, quantity=quantity, correction=correction)
        self.orders = [self.order((self.machine, 2), (self.needles, 4)), self.order((self.machine, 1), (self.thread, 5))]

    def stock(self, **data):
        request = self.selected(*self.orders, show_stock='1', supplier=self.supplier.pk, **data)
        return request, self.admin.order_stock_action(request, self.queryset(*self.orders))

    def test_own_warehouse_first_then_suppliers(self):
        _, response = self.stock(aux_supplier=self.aux.pk)
        self.assertEqual(response['Content-Type'], XLSX)
        self.assertIn("filename*=UTF-8''%D0%A13-", response['Content-Disposition'])
        self.assertEqual(sheets(response), {
            'Поставщик': [('A1', 1), ('A3', 2)],
            'Другой поставщик': [('A1', 1)],
            'Свой склад': [('A1', 1), ('A2', 4)],
            'Нет на складах': [('A3', 3)],
        })

    def test_without_auxiliary_supplier(self):
        _, response = self.stock()
        self.assertEqual(sheets(response), {
            'Поставщик': [('A1', 1), ('A3', 2)],
            'Свой склад': [('A1', 1), ('A2', 4)],
            'Нет на складах': [('A1', 1), ('A3', 3)],
        })

    def test_nothing_missing(self):
        Stock.objects.filter(product=self.thread, supplier=self.supplier).update(quantity=5)
        _, response = self.stock(aux_supplier=self.aux.pk)
        self.assertNotIn('Нет на складах', sheets(response))

    def test_orders_without_products(self):
        empty = self.order()
        request = self.selected(empty, show_stock='1', supplier=self.supplier.pk)
        self.assertIsNone(self.admin.order_stock_action(request, self.queryset(empty)))
        self.assertEqual(self.messages(request), ['Нет товаров для отгрузки у этого поставщика'])

    def test_supplier_form(self):
        request = self.selected(*self.orders)
        response = self.admin.order_stock_action(request, self.queryset(*self.orders))
        self.assertEqual(response.context_data['form'].initial, {'supplier': self.supplier.pk})

    def test_products_spreadsheet(self):
        request = self.selected(*self.orders)
        response = self.admin.order_products_action(request, self.queryset(*self.orders))
        self.assertEqual(response['Content-Type'], XLSX)
        self.assertEqual(sorted(sheets(response)['Products']), [('A1', 3), ('A2', 4), ('A3', 5)])

    def test_product_list_with_stock(self):
        query = {'orders': '%s,%s,x' % tuple(order.pk for order in self.orders), 'o': '2'}
        response = self.admin.order_product_list(self.request(query=query))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertLess(html.index('Janome'), html.index('Иглы'))  # by article
        self.assertIn('Ур:&nbsp;2<br/>С3:&nbsp;1<br/>', html)  # stock without corrections
        self.assertIn('Ур:&nbsp;<span style="color: #c00">0</span><br/>С3:&nbsp;2<br/>', html)


class ShippingTests(Base):
    def test_act_sends_collected_orders(self):
        orders = [self.order(status=Order.STATUS_COLLECTED) for _ in range(2)]
        response = self.admin.order_act_action(self.selected(*orders), self.queryset(*orders))
        act = Act.objects.get()
        self.assertEqual(response.url, reverse('admin:shop_act_change', args=[act.pk]))
        self.assertEqual(sorted(act.orders.values_list('pk', flat=True)), sorted(order.pk for order in orders))
        self.assertEqual(set(Order.objects.values_list('status', flat=True)), {Order.STATUS_SENT})

    def test_act_of_orders_not_collected(self):
        orders = [self.order(status=Order.STATUS_COLLECTED), self.order(status=Order.STATUS_ACCEPTED)]
        request = self.selected(*orders)
        self.assertIsNone(self.admin.order_act_action(request, self.queryset(*orders)))
        self.assertEqual(self.messages(request), ['Нельзя выписать акт по несобранным заказам: %s' % orders[1].pk])
        self.assertFalse(Act.objects.exists())

    def test_act_of_orders_in_another_act(self):
        order = self.order(status=Order.STATUS_COLLECTED)
        ActOrder.objects.create(act=Act.objects.create(), order=order)
        request = self.selected(order)
        self.assertIsNone(self.admin.order_act_action(request, self.queryset(order)))
        self.assertEqual(self.messages(request), ['Некоторые заказы уже описаны в других актах: %s' % order.pk])
        self.assertEqual(Act.objects.count(), 1)

    def test_1c_export_needs_contractors_warehouse_and_date(self):
        order = self.order()
        request = self.selected(order)
        self.assertIsNone(self.admin.order_1c_action(request, self.queryset(order)))
        self.assertEqual(self.messages(request), [
            'В заказах не указан контрагент: %s' % order.pk,
            'В заказах не указан склад отгрузки: %s' % order.pk,
            'В заказах не указана дата проводки: %s' % order.pk,
        ])

    def test_1c_export(self):
        warehouse = Supplier.objects.create(code='Ур', code1c='own', name='Свой склад', order=1)
        order = self.order((self.machine, 1), buyer=self.seller, wirehouse=warehouse, wiring_date=datetime.date.today())
        response = self.admin.order_1c_action(self.selected(order), self.queryset(order))
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=1C-%s.xml' % datetime.date.today().isoformat())

    def save_boxes(self, order, packed, boxes):
        """
        Saves the order's form with items packed as (product, quantity, box), and boxes with sizes entered
        as (box, {field: value}). The forms have saved what was entered before save_related().
        """
        items = FakeFormset(OrderItem, [
            SimpleNamespace(cleaned_data={'product': product, 'box': box}, instance=SimpleNamespace(quantity=quantity))
            for product, quantity, box in packed
        ])
        for box, entered in boxes:
            if box.pk is not None:
                Box.objects.filter(pk=box.pk).update(**entered)
                box.refresh_from_db()
        box_forms = FakeFormset(Box, [SimpleNamespace(cleaned_data=entered, instance=box) for box, entered in boxes])
        form = SimpleNamespace(instance=order, save_m2m=lambda: None)
        self.admin.save_related(self.request({}), form, [items, box_forms], True)

    def test_boxes_get_weight_and_sizes_of_their_items(self):
        order = self.order(delivery=Order.DELIVERY_YANDEX)
        single, mixed, weighed = (Box.objects.create(order=order) for _ in range(3))
        new = Box(order=order)  # added in the form, not saved
        nothing = {'weight': 0, 'length': 0, 'width': 0, 'height': 0}
        self.save_boxes(order, [
            (self.machine, 1, single),
            (self.needles, 2, mixed), (self.machine, 1, mixed),
            (self.needles, 1, weighed),
        ], [
            (single, nothing),
            (mixed, {**nothing, 'length': 60}),
            (weighed, {**nothing, 'weight': 7}),
            (new, nothing),
        ])
        sizes = {box.pk: (box.weight, box.length, box.width, box.height) for box in Box.objects.all()}
        self.assertEqual(sizes, {
            single.pk: (5, 50, 40, 30),  # of its only item
            mixed.pk: (5.2, 60, 0, 0),  # weight only, the items are of different sizes
            weighed.pk: (7, 10, 5, 1),  # entered weight stays
        })

    def test_boxes_only_for_yandex_delivery_and_marketplaces(self):
        order = self.order()
        box = Box.objects.create(order=order)
        self.save_boxes(order, [(self.machine, 1, box)], [(box, {'weight': 0, 'length': 0, 'width': 0, 'height': 0})])
        box.refresh_from_db()
        self.assertEqual(box.weight, 0)

    @mock.patch.dict(YandexDeliveryForm.base_fields, {'warehouse': WAREHOUSE})
    @mock.patch('shop.admin.order.create_delivery_draft_order', return_value='YD1')
    def test_yandex_delivery_recipient_name(self, create):
        for name, last_name_last, expected in (
            ('Иван', False, ('Иван', '', '')),
            ('Петров Иван', False, ('Иван', '', 'Петров')),
            ('Иван Петров', True, ('Иван', '', 'Петров')),
            ('Петров Иван Сергеевич', False, ('Иван', 'Сергеевич', 'Петров')),
            ('Иван Сергеевич Петров', True, ('Иван', 'Сергеевич', 'Петров')),
        ):
            with self.subTest(name):
                order = self.order(name=name)
                data = {'fio': name, 'warehouse': 'w1', **({'fio_last': 'on'} if last_name_last else {})}
                response = self.admin.yandex_delivery_form(self.request(data), str(order.pk))
                self.assertIn('dismissYandexDeliveryPopup(window, "%s", "YD1")' % Order.DELIVERY_YANDEX, response.content.decode())
                create.assert_called_with(order.pk, 'w1', *expected)

    @mock.patch.dict(YandexDeliveryForm.base_fields, {'warehouse': WAREHOUSE})
    @mock.patch('shop.admin.order.create_delivery_draft_order')
    def test_yandex_delivery_name_of_four_words(self, create):
        order = self.order(name='Петров Иван Сергеевич Младший')
        response = self.admin.yandex_delivery_form(self.request({'fio': order.name, 'warehouse': 'w1'}), str(order.pk))
        self.assertTrue(response.context_data['form'].errors['__all__'])
        create.assert_not_called()

    @mock.patch.dict(YandexDeliveryForm.base_fields, {'warehouse': WAREHOUSE})
    @mock.patch('shop.admin.order.create_delivery_draft_order', return_value='YD1')
    def test_yandex_delivery_needs_items_in_boxes(self, create):
        order = self.order((self.machine, 1), (self.needles, 1), name='Иван')
        data = {'fio': 'Иван', 'warehouse': 'w1'}
        response = self.admin.yandex_delivery_form(self.request(data), str(order.pk))
        self.assertEqual(response.context_data['form'].non_field_errors(), ['p1 не упакован в коробку', 'p2 не упакован в коробку'])
        create.assert_not_called()
        order.items.update(box=Box.objects.create(order=order))
        self.admin.yandex_delivery_form(self.request(data), str(order.pk))
        create.assert_called_once_with(order.pk, 'w1', 'Иван', '', '')

    @override_settings(YANDEX_DOSTAVKA={'warehouses': [{'id': 'w1', 'name': 'Склад'}]})
    @mock.patch('shop.admin.order.get_delivery_options')
    def test_yandex_delivery_options(self, options):
        options.return_value = [
            {'delivery': {'type': 'PICKUP', 'pickupPoints': [
                {'schedules': [{'from': '10:00:00', 'to': '20:00:00'}, {'from': '09:00:00', 'to': '18:00:00'}]},
                {},
            ]}, 'services': [{'name': 'insurance'}], 'cost': 300},
            {'delivery': {'type': 'COURIER', 'deliveryIntervals': [{'from': '12:00:00', 'to': '15:00:00'}]},
             'services': [], 'cost': 500},
            {'delivery': {'type': 'PICKUP', 'pickupPoints': [{}]}, 'services': [], 'cost': 200},
            {'delivery': {'type': 'PICKUP'}, 'services': [], 'cost': 100},
        ]
        order = self.order(city='Москва', postcode='101000')
        response = self.admin.yandex_delivery_estimate(self.request(), str(order.pk))
        self.assertNotIn('error', response.context_data)
        deliveries = response.context_data['deliveries']
        self.assertEqual(list(deliveries), ['PICKUP', 'COURIER'])
        [first, second, third], [courier] = deliveries['PICKUP'], deliveries['COURIER']
        self.assertEqual((first['color'], second['color'], third['color'], courier['color']), ('#1E98FF', '#1BAD03', '#FFFFFF', '#FFFFFF'))
        self.assertEqual((first['cost'], first['required_services'], first['optional_services']), (300, [{'name': 'insurance'}], []))
        self.assertEqual(first['pickupPoints'][0]['delivery_interval'], '09:00&ndash;20:00')
        self.assertNotIn('delivery_interval', first['pickupPoints'][1])
        self.assertEqual(first['delivery_interval'], '09:00&ndash;20:00')
        self.assertNotIn('delivery_interval', second)
        self.assertEqual(courier['delivery_interval'], '12:00&ndash;15:00')
        options.assert_called_once_with(order.total, False, 'w1', '101000 Москва', 10, 40, 27, 50)

    @mock.patch('beru.tasks.get_beru_labels_data')
    def test_beru_labels(self, labels):
        labels.return_value = {'orderId': 777, 'parcelBoxLabels': [{
            'fulfilmentId': 'F1', 'place': '1/1', 'weight': 2, 'deliveryServiceId': 5, 'supplierName': 'Магазин',
            'deliveryServiceName': 'INDIVIDUAL_ENTREPRENEURSHIP Иванов',
        }]}
        order = self.order()
        box = Box.objects.create(order=order)
        response = self.admin.beru_labels(self.request(), str(order.pk))
        self.assertNotIn('error', response.context_data)
        [label] = response.context_data['orders']
        self.assertEqual((label['order'], label['beru_order']), (order, labels.return_value))
        [shipment] = label['shipments']
        self.assertEqual({key: shipment[key] for key in ('id', 'code', 'place', 'weight', 'delivery_service_name', 'delivery_service_id', 'supplier_name')}, {
            'id': 'F1', 'code': box.code, 'place': '1/1', 'weight': 2, 'delivery_service_name': 'ИП Иванов',
            'delivery_service_id': 5, 'supplier_name': 'Магазин',
        })
        for svg in (label['barcode'], label['beru_barcode'], shipment['barcode']):
            self.assertTrue(svg.startswith('<svg'), svg[:40])
        self.assertNotEqual(label['barcode'], label['beru_barcode'])

    @mock.patch('beru.tasks.get_beru_labels_data', side_effect=Exception('Нет заказа'))
    def test_beru_labels_error(self, labels):
        response = self.admin.beru_labels(self.request(), str(self.order().pk))
        self.assertEqual((response.context_data['error'], response.context_data['orders']), ('Нет заказа', []))


class EditingTests(Base):
    def test_combine_orders_of_a_buyer(self):
        order, other = self.order((self.machine, 1)), self.order((self.needles, 3))
        response = self.admin.combine_form(self.request({'order_number': other.pk}), str(order.pk))
        self.assertIn('opener.dismissPopupAndReload(window)', response.content.decode())
        self.assertEqual(sorted(order.items.values_list('product', 'quantity')), [(1, 1), (2, 3)])
        self.assertEqual(list(other.items.values_list('product', 'quantity')), [(2, 3)])

    def test_combine_orders_of_different_buyers(self):
        order = self.order((self.machine, 1))
        other = self.order((self.needles, 3), user=ShopUser.objects.create(phone='+79160000000'))
        response = self.admin.combine_form(self.request({'order_number': other.pk}), str(order.pk))
        self.assertEqual(response.context_data['form'].errors['order_number'], ['Разные пользователи у заказов'])
        self.assertEqual(order.items.count(), 1)

    def discounts(self, order, **data):
        response = self.admin.discount_form(self.request(data), str(order.pk))
        self.assertIn('opener.dismissPopupAndReload(window)', response.content.decode())
        return sorted(order.items.values_list('product', 'pct_discount', 'val_discount'))

    def test_percent_discount_up_to_the_products_maximum(self):
        order = self.order((self.machine, 1), (self.needles, 1), (self.thread, 1))
        order.items.filter(product=self.thread).update(pct_discount=9)
        self.assertEqual(self.discounts(order, discount=8, unit='pct'), [(1, 8, 0), (2, 8, 0), (3, 9, 0)])
        self.assertEqual(self.discounts(order, discount=12, unit='pct'), [(1, 12, 0), (2, 10, 0), (3, 10, 0)])

    def test_discount_in_roubles(self):
        order = self.order((self.machine, 1), (self.needles, 1))
        order.items.filter(product=self.needles).update(val_discount=150)
        self.assertEqual(self.discounts(order, discount=100, unit='val'), [(1, 0, 100), (2, 0, 150)])


class FormPageTests(Base):
    """ Pages with a form: of the custom views, which the order page opens in popups, and of the actions in the list """

    @mock.patch.dict(YandexDeliveryForm.base_fields, {'warehouse': WAREHOUSE})
    def test_popup(self):
        order = self.order(name='Иван Петров')
        response = self.admin.yandex_delivery_form(self.request(query={'_popup': '1'}), str(order.pk))
        context = response.context_data
        self.assertEqual((context['is_popup'], context['title'], context['action_title']), ('1', 'Создать черновик заказа', 'Создать'))
        self.assertEqual((context['cl'], context['opts']), (self.admin, Order._meta))
        self.assertFalse(context['form'].is_bound)
        self.assertEqual(context['form'].initial, {'fio': 'Иван Петров'})
        self.assertIsNone(context['messages'])  # nothing left by other pages
        self.assertIn('Создать черновик заказа', response.render().content.decode())

    def test_failure_is_an_error_of_the_form(self):
        order = self.order()
        response = self.admin.combine_form(self.request({'order_number': 999999, '_popup': '1'}), str(order.pk))
        self.assertEqual(response.context_data['form'].errors['__all__'], ['Order matching query does not exist.'])
        self.assertEqual(response.context_data['is_popup'], '1')

    def test_invalid_form(self):
        order = self.order()
        response = self.admin.discount_form(self.request({'discount': 'много', 'unit': 'pct'}), str(order.pk))
        self.assertIn('discount', response.context_data['form'].errors)

    @mock.patch('shop.admin.order.send_message')
    def test_sms_leaves_an_empty_form(self, send):
        response = self.admin.send_sms_form(self.request({'message': 'Заказ готов', '_popup': '1'}), '+79161234567')
        send.delay.assert_called_once_with('+79161234567', 'Заказ готов')
        context = response.context_data
        self.assertEqual(context['messages'], ['Сообщение отправлено, закройте окно'])
        self.assertFalse(context['form'].is_bound)
        self.assertEqual((context['title'], context['is_popup']), ('Укажите текст сообщения для +79161234567', '1'))
        self.assertIn('Сообщение отправлено, закройте окно', response.render().content.decode())

    def test_action_forms(self):
        Supplier.objects.create(code='С3', code1c='s3', name='Поставщик', order=2)
        orders = [self.order(), self.order()]
        for action, name, title in (
            ('order_stock_action', 'show_stock', 'Выберите поставщика'),
            ('order_set_user_tag_action', 'set_user_tag', 'Укажите один или несколько тегов'),
        ):
            with self.subTest(action):
                response = getattr(self.admin, action)(self.selected(*orders), self.queryset(*orders))
                context = response.context_data
                self.assertEqual((context['action'], context['action_name'], context['title'], context['is_popup']), (action, name, title, 0))
                self.assertEqual(list(context['queryset']), orders)
                html = response.render().content.decode()
                for order in orders:
                    self.assertIn('<input type="hidden" name="_selected_action" value="%s" />' % order.pk, html)
        self.assertNotIn('messages', self.admin.order_stock_action(self.selected(*orders), self.queryset(*orders)).context_data)
