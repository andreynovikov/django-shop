from django.apps import AppConfig


class ShopAppConfig(AppConfig):
    name = 'shop'
    verbose_name = 'Магазин'

    def ready(self):
        import shop.signals  # noqa: F401
