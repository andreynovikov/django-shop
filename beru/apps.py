from django.apps import AppConfig


class BeruAppConfig(AppConfig):
    name = 'beru'
    verbose_name = 'Беру!'

    def ready(self):
        import beru.signals
