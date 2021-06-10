from django.apps import AppConfig


class SberAppConfig(AppConfig):
    name = 'sber'
    verbose_name = 'СберМаркет'

    def ready(self):
        import sber.signals
