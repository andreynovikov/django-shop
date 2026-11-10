from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from constance import config

from shop.models import Order, OrderItem, Contractor
from shop.forms import WarrantyCardForm

import logging

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


@login_required
def order_document(request, order_id, template_name):
    order = get_object_or_404(Order, pk=order_id)
    if order.user.id != request.user.id:
        """ This is not the user's order, someone tries to hack us """
        return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    context = {
        'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
        'order': order
    }
    return render(request, 'shop/order/' + template_name + '.html', context)


def print_warranty_card(request):
    if request.method == 'POST':
        form = WarrantyCardForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data['number']
            item = OrderItem.objects.filter(serial_number=number.strip()).order_by('-order__created').first()
            if item is None:
                form.add_error('number', 'Изделие с таким серийным номером не покупалось в нашем интернет-магазине')
            else:
                context = {
                    'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
                    'default_seller': Contractor.objects.filter(pk=config.sw_default_seller).first(),
                    'order': item.order,
                    'product': item.product,
                    'serial_number': item.serial_number,
                    'admin': False
                }
                return render(request, 'shop/warrantycard/common.html', context)
    else:
        form = WarrantyCardForm()

    context = {
        'form': form,
        'invalid': not form.is_valid()
    }
    return render(request, 'shop/warrantycard_form.html', context)
