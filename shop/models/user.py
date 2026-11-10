import re
import logging
import secrets

from datetime import timedelta
from math import ceil

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

# from tagging.fields import TagField

__all__ = [
    'ShopUserManager', 'ShopUser', 'LoginCode', 'PhoneCode'
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
    # Set when the owner follows the link sent to the address, or when staff enter it. Mail goes only to such addresses.
    email_verified = models.BooleanField('эл.почта подтверждена', default=False)
    # Set when a code sent to the phone comes back, or when staff enter it. Accounts created silently at checkout
    # have unproven phones.
    phone_verified = models.BooleanField('телефон подтверждён', default=False)
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


class OneTimeCode(models.Model):
    """ One-time code sent by SMS, only its hash is stored. Requesting a new code replaces the previous one. """
    LIFETIME = timedelta(minutes=5)
    RESEND_DELAY = timedelta(minutes=4)
    MAX_ATTEMPTS = 5

    code_hash = models.CharField('хэш кода', max_length=64)
    expires = models.DateTimeField('действует до')
    attempts = models.PositiveSmallIntegerField('попытки', default=0)

    class Meta:
        abstract = True

    @classmethod
    def hash_material(cls, **key):
        """ What the code is bound to, from the fields that identify the record """
        raise NotImplementedError

    @classmethod
    def hash_code(cls, code, **key):
        return salted_hmac(cls._meta.label, '%s:%s' % (cls.hash_material(**key), code), algorithm='sha256').hexdigest()

    @property
    def retry_after(self):
        """ Seconds until the code can be replaced with a new one """
        resend_at = self.expires - self.LIFETIME + self.RESEND_DELAY
        return max(0, ceil((resend_at - timezone.now()).total_seconds()))

    @property
    def attempts_left(self):
        return self.MAX_ATTEMPTS - self.attempts

    @classmethod
    def issue_code(cls, **key):
        """ Returns the code and its record, which holds only a hash of it """
        code = '%06d' % secrets.randbelow(10 ** 6)
        record, _ = cls.objects.update_or_create(**key, defaults={
            'code_hash': cls.hash_code(code, **key),
            'expires': timezone.now() + cls.LIFETIME,
            'attempts': 0,
        })
        return code, record

    @classmethod
    def verify_code(cls, code, **key):
        """ Returns True if code is valid. It is used up then, as it is when it expires or attempts run out. """
        with transaction.atomic():
            record = cls.objects.select_for_update().filter(**key).first()
            if record is None:
                return False
            expired = record.expires <= timezone.now()
            matched = not expired and constant_time_compare(record.code_hash, cls.hash_code(code, **key))
            record.attempts += 1
            if matched or expired or record.attempts >= cls.MAX_ATTEMPTS:
                record.delete()
            else:
                record.save(update_fields=['attempts'])
            return matched


class LoginCode(OneTimeCode):
    """ Code to log in, a user has at most one """
    user = models.OneToOneField(ShopUser, verbose_name='пользователь', on_delete=models.CASCADE, related_name='login_code')

    class Meta:
        verbose_name = 'код для входа'
        verbose_name_plural = 'коды для входа'

    @classmethod
    def hash_material(cls, user):
        return user.pk

    @classmethod
    def issue(cls, user):
        return cls.issue_code(user=user)

    @classmethod
    def verify(cls, user, code):
        return cls.verify_code(code, user=user)


class PhoneCode(OneTimeCode):
    """ Code that proves a phone no account has yet: to register with it, or to move the user's account to it """
    phone = models.CharField('телефон', max_length=30)
    user = models.ForeignKey(ShopUser, verbose_name='пользователь', blank=True, null=True, on_delete=models.CASCADE,
                             related_name='phone_codes', help_text='кто переходит на этот телефон, пусто при регистрации')

    class Meta:
        verbose_name = 'код подтверждения телефона'
        verbose_name_plural = 'коды подтверждения телефона'
        constraints = [
            models.UniqueConstraint(fields=['phone'], condition=models.Q(user__isnull=True), name='phonecode_registration'),
            models.UniqueConstraint(fields=['phone', 'user'], name='phonecode_change'),
        ]

    @classmethod
    def hash_material(cls, phone, user):
        # Bound to both, so a code can't prove another phone or move another account
        return '%s:%s' % (phone, user.pk if user else '')

    @classmethod
    def issue(cls, phone, user=None):
        return cls.issue_code(phone=phone, user=user)

    @classmethod
    def verify(cls, phone, code, user=None):
        return cls.verify_code(code, phone=phone, user=user)
