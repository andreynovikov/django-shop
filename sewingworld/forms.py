from django import forms

from djconfig.forms import ConfigForm


class SWConfigForm(ConfigForm):
    sw_sms_provider = forms.ChoiceField(label='Смс провайдер', initial='sms_uslugi', choices=[('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru')])
