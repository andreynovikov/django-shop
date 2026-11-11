"""
Tasks that saving an order, a page or news queues, they wait for the transaction to commit. The admin saves related
objects after the object itself, in save_related(): the items and boxes of an order, the sites of news. A task queued
at once could read them before they are saved, or act on a change that is rolled back. See settings.py on how to run.
"""
from unittest import mock

from django.contrib.sites.models import Site
from django.db import transaction
from django.test import TestCase

from beru.tasks import notify_beru_order_status
from sewingworld.models import SiteProfile
from shop.models import Box, Integration, News, Order, ShopUser
from shop.tasks.user_interaction import notify_user_order_collected

from .fixtures import add_marketplace_sites, add_product


class Rollback(Exception):
    pass


class OrderStatusTests(TestCase):
    def setUp(self):
        add_marketplace_sites()  # saving a product put in an order looks them up
        patcher = mock.patch('shop.signals.logger')  # logs every product put in an order
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = ShopUser.objects.create(phone='+79161234567')

    def order(self, **fields):
        return Order.objects.create(user=self.user, site=Site.objects.get_current(), status=Order.STATUS_ACCEPTED, **fields)

    def test_marketplace_gets_the_boxes_filled_after_the_order(self):
        market = Site.objects.create(domain='market.yandex.ru', name='Яндекс Маркет')
        integration = Integration.objects.create(name='Маркет', utm_source='beru', site=market, output_template='beru',
                                                 uses_api=True, settings={'ym_campaign': 1})
        order = self.order(integration=integration)
        order.items.create(product=add_product(1), product_price=1000, quantity=1)
        boxes_seen = []  # of the items, when the task is queued
        with mock.patch.object(notify_beru_order_status, 'delay',
                               side_effect=lambda *args: boxes_seen.append([item.box_id for item in order.items.all()])) as delay:
            with self.captureOnCommitCallbacks(execute=True):
                order.status = Order.STATUS_COLLECTED
                order.save()
                box = Box.objects.create(order=order)
                order.items.update(box=box)  # as save_related() packs the items
                delay.assert_not_called()
            delay.assert_called_once_with(order.id, 'PROCESSING', 'READY_TO_SHIP')
        self.assertEqual(boxes_seen, [[box.pk]])

    def test_customer_is_told_once_the_status_is_saved(self):
        order = self.order(payment=Order.PAYMENT_CARD)
        with mock.patch.object(notify_user_order_collected, 'delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                order.status = Order.STATUS_COLLECTED
                order.save()
                delay.assert_not_called()
            delay.assert_called_once_with(order.id)

    def test_status_rolled_back_is_not_told(self):
        order = self.order(payment=Order.PAYMENT_CARD)
        with mock.patch.object(notify_user_order_collected, 'delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises(Rollback), transaction.atomic():
                    order.status = Order.STATUS_COLLECTED
                    order.save()
                    raise Rollback
            delay.assert_not_called()


class RevalidationTests(TestCase):
    def setUp(self):
        self.main = Site.objects.get_current()
        self.other = Site.objects.create(domain='other.test', name='Другой')
        self.untokened = Site.objects.create(domain='untokened.test', name='Без токена')
        SiteProfile.objects.create(site=self.main, revalidation_token='main-token')
        SiteProfile.objects.create(site=self.other, revalidation_token='other-token')
        SiteProfile.objects.create(site=self.untokened)
        patcher = mock.patch('shop.signals.revalidate_nextjs')
        self.revalidate = patcher.start()
        self.addCleanup(patcher.stop)

    def revalidated(self):
        return sorted((call.args[0], call.args[2]['model']) for call in self.revalidate.s.call_args_list)

    def test_new_news_revalidates_the_sites_saved_after_it(self):
        with self.captureOnCommitCallbacks(execute=True):
            news = News.objects.create(title='Новость', content='Текст', active=True)
            news.sites.set([self.main, self.untokened])  # as save_related() saves them
            self.revalidate.s.assert_not_called()
        self.assertEqual(self.revalidated(), [(self.main.domain, 'news')])
        self.assertEqual(self.revalidate.s.call_args.args[1:], ('main-token', {'model': 'news', 'pk': news.pk}))

    def test_news_moved_to_another_site_revalidates_both(self):
        news = News.objects.create(title='Новость', content='Текст', active=True)
        news.sites.set([self.main])
        with self.captureOnCommitCallbacks(execute=True):
            news.title = 'Новость о другом'
            news.save()
            news.sites.set([self.other])
        self.assertEqual(self.revalidated(), [(self.main.domain, 'news'), (self.other.domain, 'news')])
