import re
import logging

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

# from tagging.fields import TagField

__all__ = [
    'ShopUserManager', 'ShopUser'
]

logger = logging.getLogger(__name__)


class ShopUserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError('Users must have a phone')

        user = self.model(phone=self.normalize_phone(phone),)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password):
        user = self.create_user(phone, password=password,)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_phone(phone):
        phone = re.sub(r"[^0-9\+]", "", phone)
        if not phone.startswith("+"):
            if phone.startswith("7") and len(phone) == 11:
                phone = "+" + phone
            else:
                phone = "+7" + phone
        return phone

    @staticmethod
    def format_phone(phone):
        m = re.match(r"(\+7)(\d{3})(\d{3})(\d{2})(\d{2})", phone)
        if not m:
            m = re.match(r"(\+7)(\d{3})(\d.{2})(.{2})(\d{2})", phone)
            if not m:
                return phone
        return "{0} ({1}) {2}-{3}-{4}".format(*m.groups())


class AliasField(models.Field):
    def contribute_to_class(self, cls, name, private_only=False):
        ''' virtual_only is deprecated in favor of private_only '''
        super(AliasField, self).contribute_to_class(cls, name, private_only=True)
        setattr(cls, name, self)


class UsernameField(models.CharField):
    description = "CharField that stores NULL but returns ''"

    def __init__(self, *args, **kwargs):
        kwargs['unique'] = True
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['default'] = ''
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['unique']
        del kwargs['null']
        del kwargs['blank']
        del kwargs['default']
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        return value or ''

    def get_db_prep_value(self, value, connection, prepared=False):
        return value or None


class ShopUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField('телефон', max_length=30, unique=True)
    name = models.CharField('имя', max_length=100, blank=True)
    username = UsernameField('псевдоним', max_length=100)
    email = models.EmailField('эл.почта', blank=True)
    postcode = models.CharField('индекс', max_length=10, blank=True)
    city = models.CharField('город', max_length=255, blank=True)
    address = models.CharField('адрес', max_length=255, blank=True)
    discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    bonuses = models.PositiveIntegerField('бонусы', default=0)
    expiring_bonuses = models.PositiveIntegerField('сгорающие бонусы', default=0)
    expiration_date = models.DateTimeField('дата сгорания бонусов', blank=True, null=True)
    is_active = models.BooleanField('активный', default=True)
    is_staff = models.BooleanField('сотрудник', default=False)
    permanent_password = models.BooleanField('постоянный пароль', default=False)
    date_joined = models.DateTimeField('дата регистрации', default=timezone.now)
    tags = models.CharField('теги', max_length=255, blank=True)  # TagField('теги')
    first_name = AliasField(db_column='name', blank=True)
    last_name = AliasField(db_column='name', blank=True)

    objects = ShopUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        permissions = (
            ('wholesale', "Может покупать оптом"),
        )

    @staticmethod
    def autocomplete_search_fields():
        return ['id__iexact', 'name__icontains', 'phone__icontains', 'email__icontains']

    def get_short_name(self):
        return self.name or self.phone

    def get_full_name(self):
        return self.username or self.name or ShopUserManager.format_phone(self.phone[:-6] + '****' + self.phone[-2:])

    def __str__(self):
        return self.get_short_name()

    def related_label(self):
        if self.name:
            return "%s (%s)" % (self.name, self.phone)
        else:
            return self.phone
