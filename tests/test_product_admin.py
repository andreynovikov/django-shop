"""
Saving a product in the admin, beyond what Django does. See settings.py on how to run.
"""
from unittest import mock

from django.contrib.admin.sites import site as admin_site
from django.test import RequestFactory, TestCase

from shop.models import Product
from shop.tasks.workflow import post_update_product

from .fixtures import add_marketplace_sites, add_product


class ProductSaveTests(TestCase):
    def test_update_task_is_queued_after_commit(self):
        """
        The task reads the sites that save_related() sets after save_model(). Queued inside the admin's transaction,
        the worker could read the old ones, and its insert of the task's row waited for that transaction.
        """
        add_marketplace_sites()  # integrations look them up when a product is saved
        product = add_product(1)
        with mock.patch.object(post_update_product, 'delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                admin_site._registry[Product].save_model(RequestFactory().post('/'), product, form=None, change=True)
                delay.assert_not_called()
            delay.assert_called_once_with(1, 'admin')
