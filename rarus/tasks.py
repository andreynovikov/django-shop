import json
import logging

from hashlib import sha1
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import django.db
from django.conf import settings
from django.utils import timezone

from celery import shared_task

from shop.models import ShopUser, Bonus


logger = logging.getLogger('rarus')

RARUS = getattr(settings, 'RARUS', {})
HOST = 'https://bonus.rarus-online.com:88'


class TaskFailure(Exception):
    pass


def get_token():
    data = {
        'login': RARUS.get('login', ''),
        'password': sha1(RARUS.get('password', '').encode()).hexdigest(),
        'role': 'organization'
    }
    data_encoded = json.dumps(data).encode('utf-8')
    url = '{}/sign_in'.format(HOST)
    headers = {
        'Content-Type': 'application/json;charset=UTF-8'
    }

    request = Request(url, data_encoded, headers, method='POST')
    logger.info('<<< ' + request.full_url)
    response = urlopen(request)
    result = json.loads(response.read().decode('utf-8'))
    logger.debug(result)
    return result.get('token', '')


def get_cards():
    url = '{}/organization/card'.format(HOST)
    headers = {
        'Token': get_token(),
        'Content-Type': 'application/json;charset=UTF-8'
    }

    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        print(result)
        logger.debug(result)
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        raise TaskFailure(error) from e


@shared_task(autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def get_bonus_value(phone):
    user = ShopUser.objects.get(phone=phone)
    if not hasattr(user, 'bonus'):
        user.bonus = Bonus()
    user.bonus.updated = timezone.now()

    url = '{}/organization/card/by_phone?filter={}'.format(HOST, phone[1:])  # remove '+' from phone number
    headers = {
        'Token': get_token(),
        'Content-Type': 'application/json;charset=UTF-8'
    }

    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
    except HTTPError as e:
        if e.code == 404:
            user.bonus.value = 0
            user.bonus.status = Bonus.STATUS_OK
            user.bonus.save()
            return
        user.bonus.status = Bonus.STATUS_UNDEFINED
        user.bonus.save()
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        raise TaskFailure(error) from e

    if result.get('code', -1) != 0:
        user.bonus.status = Bonus.STATUS_UNDEFINED
        user.bonus.save()
        return

    balance = 0
    for card in result.get('cards', []):
        # active = card.get('active', False)
        # blocked = card.get('blocked', False)
        # if active and not blocked:
        balance += card.get('actual_balance', 0)

    user.bonus.value = balance
    user.bonus.status = Bonus.STATUS_OK
    user.bonus.save()
