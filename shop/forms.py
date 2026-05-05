from django import forms

from reviews.forms import ReviewForm


class ProductReviewForm(ReviewForm):
    def __init__(self, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)
        self.fields['comment'].required = False


class WarrantyCardForm(forms.Form):
    number = forms.CharField(label='Серийный номер', max_length=100,
                             help_text='Серийный номер можно найти на корпусе изделия или в гарантийном талоне',
                             error_messages={'required': 'Укажите серийный номер изделия'})
