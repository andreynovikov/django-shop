import re
import logging
import secrets

from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

# from tagging.fields import TagField

__all__ = [
    'ShopUserManager', 'ShopUser', 'LoginCode'
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


class LoginCode(models.Model):
    """ One-time code sent by SMS, a user has at most one: requesting a new code replaces the previous """
    LIFETIME = timedelta(minutes=5)
    MAX_ATTEMPTS = 5

    user = models.OneToOneField(ShopUser, verbose_name='пользователь', on_delete=models.CASCADE, related_name='login_code')
    code_hash = models.CharField('хэш кода', max_length=64)
    expires = models.DateTimeField('действует до')
    attempts = models.PositiveSmallIntegerField('попытки', default=0)

    class Meta:
        verbose_name = 'код для входа'
        verbose_name_plural = 'коды для входа'

    @staticmethod
    def hash_code(user, code):
        return salted_hmac('shop.LoginCode', '%s:%s' % (user.pk, code), algorithm='sha256').hexdigest()

    @classmethod
    def issue(cls, user):
        code = '%06d' % secrets.randbelow(10 ** 6)
        cls.objects.update_or_create(user=user, defaults={
            'code_hash': cls.hash_code(user, code),
            'expires': timezone.now() + cls.LIFETIME,
            'attempts': 0,
        })
        return code

    @classmethod
    def verify(cls, user, code):
        """ Returns True if code is valid. It is used up then, as it is when it expires or attempts run out. """
        with transaction.atomic():
            login_code = cls.objects.select_for_update().filter(user=user).first()
            if login_code is None:
                return False
            expired = login_code.expires <= timezone.now()
            matched = not expired and constant_time_compare(login_code.code_hash, cls.hash_code(user, code))
            login_code.attempts += 1
            if matched or expired or login_code.attempts >= cls.MAX_ATTEMPTS:
                login_code.delete()
            else:
                login_code.save(update_fields=['attempts'])
            return matched
