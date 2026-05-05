import re

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core import signing
from django.urls import reverse

from djconfig import config

from shop.models import Product, Basket, Order, OrderItem
from shop.forms import WarrantyCardForm

import logging

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def restore_basket(request, restore):
    ensure_session(request)
    basket, created = Basket.objects.get_or_create(site=Site.objects.get_current(), session_id=request.session.session_key)
    if created:
        contents = map(lambda p: map(int, p.split('*')), restore.split(','))
        import sys
        for product_id, quantity in contents:
            print('%d: %d' % (product_id, quantity), file=sys.stderr)
            try:
                product = Product.objects.get(pk=product_id)
                item, _ = basket.items.get_or_create(product=product)
                item.quantity = quantity
                item.save()
            except Product.DoesNotExist:
                pass
        utm_source = request.GET.get('utm_source', None)
        if utm_source:
            basket.utm_source = re.sub(r'(?a)[^\w]', '_', utm_source)  # ASCII only regex
        basket.secondary = True
        basket.save()
    query_string = request.GET.urlencode()
    if query_string:
        query_string = '?' + query_string
    return HttpResponseRedirect(reverse('shop:basket') + query_string)


def clear_basket(request, basket_sign):
    signer = signing.Signer()
    try:
        basket_id = signer.unsign(basket_sign)
        basket = Basket.objects.get(pk=basket_id)
        basket.delete()
    except signing.BadSignature:
        return HttpResponseForbidden()
    except Basket.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('shop:basket'))


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
                    'default_seller': config.sw_default_seller,
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
