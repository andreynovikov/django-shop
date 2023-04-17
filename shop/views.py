import json
import re

from math import ceil
from random import randint
from decimal import Decimal, ROUND_HALF_EVEN
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.models import Site
from django_ipgeobase.models import IPGeoBase
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core import signing
from django.core.mail import mail_admins
from django.urls import reverse
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from django.utils.formats import localize

from sewingworld.tasks import PRIORITY_HIGHEST, PRIORITY_IDLE

from facebook.tasks import FACEBOOK_TRACKING, notify_add_to_cart, notify_initiate_checkout, notify_purchase
from shop.tasks import send_password, notify_user_order_new_sms, notify_user_order_new_mail
from shop.models import Product, Basket, BasketItem, Order, OrderItem, ShopUser, ShopUserManager
from shop.forms import UserForm, WarrantyCardForm

import logging

logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def index(request):
    products = Product.objects.order_by('-title')
    context = {'products': products}
    return render(request, 'shop/index.html', context)


def view_promo(request):
    ensure_session(request)
    promo = None
    promo = request.META['QUERY_STRING']
    promos = getattr(settings, 'SHOP_PROMOTIONS', {})
    discount = promos.get(promo, 0)
    request.session['discount'] = discount
    context = {'promo': promo, 'discount': discount}
    return render(request, 'shop/promo.html', context)


def view_empty_basket(request):
    ensure_session(request)
    context = {}
    return render(request, 'shop/empty.html', context)


def view_basket_notice(request):
    ensure_session(request)
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        basket = None
    context = {
        'basket': basket
    }
    return render(request, 'shop/notice.html', context)


def view_basket_notice_new(request):
    ensure_session(request)
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        basket = None
    context = {
        'basket': basket
    }
    return render(request, 'shop/notice_new.html', context)


def view_basket_extnotice(request):
    ensure_session(request)
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        basket = None
    context = {
        'basket': basket
    }
    product_id = request.GET.get('product', None)
    if product_id and basket is not None and basket.items.count() > 4:
        context['collapse'] = True
        context['added_product'] = int(product_id)
        context['other_count'] = basket.items.count() - 1
    return render(request, 'shop/extnotice.html', context)


def view_basket(request):
    ensure_session(request)
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        if request.session.get('last_order', None):
            return HttpResponseRedirect(reverse('shop:user_orders'))
        else:
            return HttpResponseRedirect(reverse('shop:empty'))
    phone = basket.phone
    full_phone = None
    user = None
    user_id = None
    if phone:
        norm_phone = ShopUserManager.normalize_phone(phone)
        full_phone = ShopUserManager.format_phone(phone)
        try:
            user = ShopUser.objects.get(phone=norm_phone)
            user_id = user.id
        except ShopUser.DoesNotExist:
            pass

    if FACEBOOK_TRACKING:
        notify_initiate_checkout.s(
            basket.id, user_id, request.build_absolute_uri(),
            request.META.get('REMOTE_ADDR'),
            request.META['HTTP_USER_AGENT']).apply_async(priority=PRIORITY_IDLE)
    context = {
        'basket': basket,
        'shop_user': user,
        'phone': phone,
        'full_phone': full_phone,
        'wrong_password': request.GET.get('wrong_password', '0') == '1'
    }
    return render(request, 'shop/basket.html', context)


def add_to_basket(request, product_id):
    ensure_session(request)
    product = get_object_or_404(Product, pk=product_id)
    basket, created = Basket.objects.get_or_create(site=Site.objects.get_current(), session_id=request.session.session_key)
    item, created = basket.items.get_or_create(product=product)
    if not created:
        item.quantity += 1
    item.save()
    utm_source = request.GET.get('utm_source', None)
    if utm_source:
        basket.utm_source = re.sub(r'(?a)[^\w]', '_', utm_source)  # ASCII only regex
        basket.save()

    if FACEBOOK_TRACKING:
        notify_add_to_cart.s(
            product.id, request.build_absolute_uri(),
            request.META.get('REMOTE_ADDR'),
            request.META['HTTP_USER_AGENT']).apply_async(priority=PRIORITY_IDLE)

    # as soon as user starts gethering new basket "forget" last order
    try:
        del request.session['last_order']
    except KeyError:
        pass
    if request.GET.get('silent'):
        return HttpResponse(status=204)
    else:
        return HttpResponseRedirect(reverse('shop:basket'))


def around(x, base=10):
    return int(base * ceil(float(x) / base))


@require_POST
def update_basket(request, product_id):
    ensure_session(request)
    product = get_object_or_404(Product, pk=product_id)
    basket, created = Basket.objects.get_or_create(site=Site.objects.get_current(), session_id=request.session.session_key)
    quantity = 0
    item, created = basket.items.get_or_create(product=product)
    try:
        quantity = int(request.POST.get('quantity'))
        if quantity <= 0:
            quantity = 0
    except ValueError:
        quantity = item.quantity
    if quantity == 0:
        item.delete()
    else:
        if WHOLESALE and product.ws_pack_only:
            quantity = around(quantity, product.pack_factor)
        item.quantity = quantity
        item.save()

    if basket.items.count() == 0:
        basket.delete()
    if request.POST.get('ajax'):
        if WHOLESALE:
            qnt = Decimal('0.01')
        else:
            qnt = Decimal('1')
        data = {
            'quantity': quantity,
            'fragments': {
                '#total': '<span id="total">' + localize(basket.total.quantize(qnt, rounding=ROUND_HALF_EVEN)) + '</span>'
            }
        }
        if quantity > 0:
            product_id = str(item.product.id)
            data['fragments']['#price_' + product_id] = \
                '<span id="price_' + product_id + '">' + \
                localize(item.price.quantize(qnt, rounding=ROUND_HALF_EVEN)) + '</span>'
            notice = "Не всё количество есть на складе" if quantity > item.product.instock and item.product.instock > 0 else ""
            data['fragments']['#notice_' + product_id] = \
                '<span id="notice_' + product_id + '">' + notice + '</span>'
        return JsonResponse(data)
    else:
        return HttpResponseRedirect(reverse('shop:basket'))


def delete_from_basket(request, product_id):
    ensure_session(request)
    product = get_object_or_404(Product, pk=product_id)
    basket = get_object_or_404(Basket, session_id=request.session.session_key)
    try:
        item = basket.items.get(product=product)
        item.delete()
    except BasketItem.DoesNotExist:
        pass
    basket.save()
    if basket.items.count() == 0:
        basket.delete()
        basket = None
    if request.GET.get('ajax'):
        if basket:
            if WHOLESALE:
                qnt = Decimal('0.01')
            else:
                qnt = Decimal('1')
            data = {
                'fragments': {
                    '#total': '<span id="total">' + localize(basket.total.quantize(qnt, rounding=ROUND_HALF_EVEN)) + '</span>'
                }
            }
        else:
            data = {
                'location': reverse('shop:basket')
            }
        return JsonResponse(data)
    else:
        return HttpResponseRedirect(reverse('shop:basket'))


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


@require_POST
def authorize(request):
    ensure_session(request)
    basket = get_object_or_404(Basket, session_id=request.session.session_key)
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    request.session['meta'] = request.POST.get('meta')
    data = None

    if password:
        norm_phone = ShopUserManager.normalize_phone(basket.phone)
        user = authenticate(username=norm_phone, password=password)
        if user and user.is_active:
            login(request, user)
            basket.update_session(request.session.session_key)
            """
            We disabled this because Nikolay wants order to be registered as soon as user authenticates
            data = {
                'user': user,
            }
            """
        else:
            """ Bad password """
            data = {
                'shop_user': ShopUser.objects.get(phone=norm_phone),
                'wrong_password': True
            }

    if phone:
        norm_phone = ShopUserManager.normalize_phone(phone)
        basket.phone = norm_phone
        basket.save()
        user, created = ShopUser.objects.get_or_create(phone=norm_phone)
        if not user.permanent_password:
            """ Generate new password for user """
            password = str(randint(1000, 9999))
            user.set_password(password)
            user.save()
        if created:
            """ Login new user """
            user = authenticate(username=norm_phone, password=password)
            login(request, user)
            basket.update_session(request.session.session_key)
            request.session['password'] = password
        else:
            """ User exists, request password """
            if not user.permanent_password:
                try:
                    send_password.s(norm_phone, password).apply_async(priority=PRIORITY_HIGHEST)
                except Exception as e:
                    mail_admins('Task error', 'Failed to send password: %s' % e, fail_silently=True)
            data = {
                'shop_user': user,
            }

    if request.user.is_authenticated and not data:
        if request.POST.get('ajax'):
            return JsonResponse({'location': reverse('shop:confirm')})
        else:
            return HttpResponseRedirect(reverse('shop:confirm'))
    else:
        if request.POST.get('ajax'):
            data = {
                'html': render_to_string('shop/_send_order.html', data, request),
            }
            return JsonResponse(data)
        elif data and 'wrong_password' in data:
            return HttpResponseRedirect(reverse('shop:basket') + '?wrong_password=1')
        else:
            return HttpResponseRedirect(reverse('shop:basket'))


def register_user(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        norm_phone = ShopUserManager.normalize_phone(phone)
        next_url = request.POST.get('next')
        if norm_phone:
            try:
                user = ShopUser.objects.get(phone=norm_phone)
                context = {
                    'phone': phone,
                    'email': request.POST.get('email'),
                    'name': request.POST.get('name'),
                    'username': request.POST.get('username'),
                    'next': next_url,
                    'error': 'Пользователь с таким телефоном уже зарегистрирован'
                }
            except ShopUser.DoesNotExist:
                # create user, it will be authorized later by login
                try:
                    user = ShopUser(phone=norm_phone)
                    user.email = request.POST.get('email')
                    user.name = request.POST.get('name')
                    user.username = request.POST.get('username')
                    user.save()
                    params = {
                        'phone': norm_phone,
                        'next': next_url,
                        'reg': request.POST.get('reg') or '1'
                    }
                    return HttpResponseRedirect(reverse('shop:login') + '?' + urlencode(params))
                except IntegrityError:
                    logger.exception("An error occurred")
                    context = {
                        'phone': phone,
                        'email': request.POST.get('email'),
                        'name': request.POST.get('name'),
                        'username': request.POST.get('username'),
                        'next': next_url,
                        'error': 'Пользователь с таким именем уже зарегистрирован'
                    }
    else:
        context = {
            'next': request.GET.get('next')
        }
    return render(request, 'shop/register.html', context)


def login_user(request):
    """
    Login user preserving his basket
    """
    norm_phone = None
    password = None
    reg = None

    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        next_url = request.POST.get('next')
        reg = request.POST.get('reg')
    else:
        phone = request.GET.get('phone')
        next_url = request.GET.get('next')
        reg = request.GET.get('reg')

    if phone:
        norm_phone = ShopUserManager.normalize_phone(phone)

    if norm_phone and password:
        try:
            basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
        except MultipleObjectsReturned:
            basket = None
        except Basket.DoesNotExist:
            basket = None
        user = authenticate(username=norm_phone, password=password)
        if user and user.is_active:
            permanent_password = request.POST.get('permanent_password')
            if permanent_password:
                user.set_password(permanent_password)
                user.permanent_password = True
                user.save()
            login(request, user)
            if basket:
                basket.update_session(request.session.session_key)
                basket.phone = user.phone
                basket.save()
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        try:
            user = ShopUser.objects.get(phone=norm_phone)
        except ShopUser.DoesNotExist:
            user = None
        context = {
            'phone': phone,
            'shop_user': user,
            'next': next_url,
            'reg': reg,
            'wrong_password': True
        }
    elif norm_phone:
        try:
            user = ShopUser.objects.get(phone=norm_phone)
            if not user.permanent_password:
                """ Generate new password for user """
                password = str(randint(1000, 9999))
                user.set_password(password)
                user.save()
                try:
                    if reg != '1':
                        send_password.s(norm_phone, password).apply_async(priority=PRIORITY_HIGHEST)
                except Exception as e:
                    mail_admins('Task error', 'Failed to send password: %s' % e, fail_silently=True)
            context = {
                'phone': phone,
                'shop_user': user,
                'reg': reg,
                'next': next_url
            }
        except ShopUser.DoesNotExist:
            context = {
                'phone': phone,
                'next': next_url,
                'reg': reg,
                'error': 'Пользователь с таким телефоном не зарегистрирован'
            }
    else:
        context = {
            'reg': reg,
            'next': request.GET.get('next')
        }
    return render(request, 'shop/login.html', context)


@login_required
def logout_user(request):
    """
    Logout user preserving his basket contents
    """
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        basket = None
    logout(request)
    ensure_session(request)
    # do not copy cart contents for wholesale user
    if basket and not WHOLESALE:
        basket.update_session(request.session.session_key)
        basket.phone = ''
        basket.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def unbind(request):
    """
    Remove phone binding from basket
    """
    ensure_session(request)
    basket = get_object_or_404(Basket, session_id=request.session.session_key)
    basket.phone = ''
    basket.save()
    if request.GET.get('ajax'):
        return JsonResponse(None, safe=False)
    else:
        return HttpResponseRedirect(reverse('shop:basket'))


def reset_password(request):
    """
    Generate new password and send it to user by sms
    """
    ensure_session(request)
    phone = request.GET.get('phone', None)
    if phone:
        phone = ShopUserManager.normalize_phone(phone)
    else:
        basket = get_object_or_404(Basket, session_id=request.session.session_key)
        if basket.phone:
            phone = basket.phone
    if phone:
        password = str(randint(1000, 9999))
        try:
            user = ShopUser.objects.get(phone=phone)
        except ShopUser.DoesNotExist:
            return HttpResponseNotFound()
        user.set_password(password)
        user.permanent_password = False
        user.save()
        try:
            send_password.s(phone, password).apply_async(priority=PRIORITY_HIGHEST)
        except Exception as e:
            mail_admins('Task error', 'Failed to send password: %s' % e, fail_silently=True)
    else:
        """ we can not reset password if phone is not known yet """
        return HttpResponseForbidden()
    if request.GET.get('ajax'):
        return JsonResponse(None, safe=False)
    else:
        return HttpResponseRedirect(reverse('shop:basket'))


@login_required
def confirm_order(request, order_id=None):
    try:
        basket = Basket.objects.get(site=Site.objects.get_current(), session_id=request.session.session_key)
    except Basket.DoesNotExist:
        basket = None

    if order_id or basket is None:
        """ order is already confirmed, it's just the reload """
        if order_id is None:
            order_id = request.session.get('last_order', None)
        order = get_object_or_404(Order, pk=order_id)
        if order.user.id != request.user.id:
            """ This is not the user's order """
            return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
        context = {
            'order': order,
            'updated': request.session.get('last_order_updated', False)
        }
    else:
        """ register order """
        try:
            order = Order.register(basket)
            ipgeobases = IPGeoBase.objects.by_ip(request.META.get('REMOTE_ADDR'))
            if ipgeobases.exists():
                for ipgeobase in ipgeobases:
                    if ipgeobase.city is not None:
                        order.city = ipgeobase.city
                        break
            if request.session['meta']:
                order.meta = json.loads(request.session['meta'])
            order.save()
            request.session['last_order'] = order.id
            request.session['last_order_updated'] = False
            """ wait for 5 minutes to let user supply comments and other stuff """
            try:
                notify_user_order_new_mail.apply_async((order.id,), countdown=300)
                notify_user_order_new_sms.apply_async((order.id, request.session.get('password', None)), countdown=300)
            except Exception as e:
                mail_admins('Task error', 'Failed to send notification: %s' % e, fail_silently=True)
            basket.delete()

            if FACEBOOK_TRACKING:
                notify_purchase.s(
                    order.id, request.build_absolute_uri(),
                    request.META.get('REMOTE_ADDR'),
                    request.META['HTTP_USER_AGENT']).apply_async(priority=PRIORITY_IDLE)
            """ clear promo discount """
            try:
                del request.session['discount']
            except KeyError:
                pass
            context = {
                'order': order
            }
        except Exception as e:
            mail_admins('Order error', 'Failed to register order: %s' % e, fail_silently=True)
            return HttpResponseServerError("Failed to register order: %s" % e)
    return render(request, 'shop/order_confirmation.html', context)


@require_POST
@login_required
def update_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.user.id != request.user.id:
        """ This is not the user's order """
        return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    if not request.user.name:
        request.user.name = request.POST.get('name')
    order.name = request.POST.get('name') or request.user.name
    if not request.user.email:
        request.user.email = request.POST.get('email')
    order.email = request.POST.get('email') or request.user.email
    if not request.user.address:
        request.user.address = request.POST.get('address')
    order.address = request.POST.get('address') or request.user.address
    if request.POST.get('city'):
        order.city = request.POST.get('city')
    order.postcode = request.POST.get('postcode')
    order.comment = request.POST.get('comment')
    order.save()
    request.user.save()
    request.session['last_order_updated'] = True
    try:
        del request.session['password']
    except KeyError:
        pass
    context = {
        'order': order,
        'updated': True
    }
    data = {
        'html': render_to_string('shop/_update_order.html', context, request),
    }
    if request.POST.get('ajax'):
        return JsonResponse(data)
    else:
        return HttpResponseRedirect(reverse('shop:confirm', args=[order.id]))


@login_required
def orders(request):
    orders = Order.objects.order_by('-id').filter(user=request.user.id)
    form = UserForm(user=request.user)
    context = {
        'orders': orders,
        'user_form': form
    }
    return render(request, 'shop/user_orders.html', context)


@login_required
def order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.user.id != request.user.id:
        """ This is not the user's order """
        return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    context = {
        'order': order
    }
    return render(request, 'shop/order.html', context)


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


@login_required
def update_user(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, user=user)
        if form.is_valid():
            user.name = form.cleaned_data['name']
            user.phone = ShopUserManager.normalize_phone(form.cleaned_data['phone'])
            user.email = form.cleaned_data['email']
            user.address = form.cleaned_data['address']
            user.username = form.cleaned_data['username']
            user.save()
    else:
        form = UserForm(user=user)

    context = {
        'user_form': form,
        'invalid': not form.is_valid(),
        'update': not request.GET.get('update') is None
    }
    if request.GET.get('ajax') or request.POST.get('ajax'):
        data = {
            'html': render_to_string('shop/_update_user.html', context, request),
        }
        return JsonResponse(data)
    else:
        return render(request, 'shop/_update_user.html', context)


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
