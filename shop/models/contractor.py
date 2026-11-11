from django.db import models

__all__ = ['Contractor', 'PosTerminal']


class Contractor(models.Model):
    # numerical values taken from https://yookassa.ru/developers/payment-acceptance/receipts/54fz/other-services/parameters-values
    TAX_SYSTEM_GTS = 1
    TAX_SYSTEM_STS = 2
    TAX_SYSTEM_CHOICES = (
        (TAX_SYSTEM_GTS, 'ОСН'),
        (TAX_SYSTEM_STS, 'УСН'),
    )
    VAT_RATE_NONE = 1
    VAT_RATE_0 = 2
    VAT_RATE_10 = 3
    VAT_RATE_20 = 4
    VAT_RATE_5 = 7
    VAT_RATE_7 = 8
    VAT_RATE_22 = 11
    VAT_RATE_CHOICES = (
        (VAT_RATE_NONE, 'Без НДС'),
        (VAT_RATE_0, 'НДС по ставке 0%'),
        (VAT_RATE_5, 'НДС по ставке 5%'),
        (VAT_RATE_7, 'НДС по ставке 7%'),
        (VAT_RATE_10, 'НДС по ставке 10%'),
        (VAT_RATE_20, 'НДС по ставке 20%'),
        (VAT_RATE_22, 'НДС по ставке 22%'),
    )
    code = models.CharField('код 1С', max_length=64)
    name = models.CharField('название', max_length=100)
    is_seller = models.BooleanField('продавец', default=False)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    ogrn = models.CharField('ОГРН', max_length=13, blank=True)
    tax_system = models.SmallIntegerField('система налогообложения', choices=TAX_SYSTEM_CHOICES, blank=True, null=True)
    vat_rate = models.SmallIntegerField('ставка НДС', choices=VAT_RATE_CHOICES, blank=True, null=True)
    legal_address = models.TextField('юр. адрес', blank=True)
    postal_address = models.TextField('физ. адрес', blank=True)
    bank_requisites = models.TextField('банковские реквизиты', blank=True)
    stamp = models.ImageField('печать', upload_to='contractors', blank=True)
    script = models.ImageField('подпись', upload_to='contractors', blank=True)
    yookassa_id = models.CharField('ID аккаунта ЮKassa', max_length=20, blank=True)
    yookassa_key = models.CharField('секретный ключ ЮKassa', max_length=255, blank=True)
    modulkassa_login = models.CharField('логин МодульКасса', max_length=255, blank=True)
    modulkassa_password = models.CharField('пароль МодульКасса', max_length=255, blank=True)

    class Meta:
        verbose_name = 'контрагент'
        verbose_name_plural = 'контрагенты'

    def __str__(self):
        return self.name


class PosTerminal(models.Model):
    id = models.CharField('идентификатор кассы', max_length=100, primary_key=True)
    seller = models.ForeignKey(Contractor, verbose_name='продавец', on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'pos-терминал'
        verbose_name_plural = 'pos-терминалы'

    def __str__(self):
        return self.id
