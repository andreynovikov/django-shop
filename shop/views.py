import re

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core import signing

from constance import config

from shop.models import Product, Basket, Order, OrderItem, Contractor
from shop.forms import WarrantyCardForm

import logging

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def parse_restore(restore):
    """ Parse '<product_id>*<quantity>,...' into a dict, skipping malformed entries """
    contents = {}
    for part in restore.split(','):
        match = re.fullmatch(r'(\d{1,9})\*(\d{1,5})', part.strip())
        if not match:
            continue
        product_id, quantity = map(int, match.groups())
        if 0 < quantity <= 32767:  # PositiveSmallIntegerField range
            contents[product_id] = quantity
    return contents


def restore_basket(request, restore):
    ensure_session(request)
    contents = parse_restore(restore)
    basket, created = Basket.objects.get_or_create(site=Site.objects.get_current(), session_id=request.session.session_key)
    if created:
        for product in Product.objects.filter(pk__in=contents.keys()):
            item, _ = basket.items.get_or_create(product=product)
            item.quantity = contents[product.id]
            item.save()
        utm_source = request.GET.get('utm_source', None)
        if utm_source:
            basket.utm_source = re.sub(r'(?a)[^\w]', '_', utm_source)  # ASCII only regex
        basket.secondary = True
        basket.save()
    query_string = request.GET.urlencode()
    if query_string:
        query_string = '?' + query_string
    return HttpResponseRedirect('/cart/' + query_string)


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
    return HttpResponseRedirect('/cart/')


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
