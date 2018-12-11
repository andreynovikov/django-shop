from collections import OrderedDict
from django.apps import AppConfig
from django.forms import CharField

class ForumAppConfig(AppConfig):
    name = 'forum'
    verbose_name = 'Форум'

    """
    def ready(self):
        from spirit.user.forms import UserForm
        UserForm._meta.fields = ('username',)
        UserForm.base_fields = OrderedDict([('username', CharField(label='Псевдоним', required=False, max_length=100))])
    """
