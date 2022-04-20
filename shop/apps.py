from collections import OrderedDict
from django.apps import AppConfig
from django.forms import CharField

class ShopAppConfig(AppConfig):
    name = 'shop'
    verbose_name = 'Магазин'

    def ready(self):
        import shop.signals
