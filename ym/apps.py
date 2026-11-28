from django.apps import AppConfig


class YandexMarketAppConfig(AppConfig):
    name = 'ym'
    verbose_name = 'Яндекс Маркет'

    def ready(self):
        import ym.signals  # noqa: F401
