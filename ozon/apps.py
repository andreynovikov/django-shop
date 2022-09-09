from django.apps import AppConfig


class OzonAppConfig(AppConfig):
    name = 'ozon'
    verbose_name = 'Ozon'

    def ready(self):
        import ozon.signals
