from django.apps import AppConfig


class WildberriesAppConfig(AppConfig):
    name = 'wb'
    verbose_name = 'Wildberries'

    def ready(self):
        import wb.signals
