"""
Stock and prices from 1C: its export comes to Yandex Disk, update_1c_stocks() fetches it and import1c() reads it.
"""
import csv
import hashlib
import json
import logging
import os
import re
import tempfile

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection, Error as DatabaseError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import dateparse, timezone

from celery import shared_task

from constance import config
from flags.state import enable_flag, disable_flag

from sewingworld.tasks import single_instance_task

from shop.models import Supplier, Currency, Product, Stock, Order

from .common import get_default_site
from .workflow import post_update_products


log = logging.getLogger('shop')


@shared_task(name='shop.tasks.update_1c_stocks', bind=True, queue="import", autoretry_for=(OSError, DatabaseError), retry_backoff=300, retry_jitter=False)
def update_1c_stocks(self):
    filename = 'ВыгрузкаНаСайтПоВсемСкладамПромимпекс.csv'
    url = 'https://cloud-api.yandex.net/v1/disk/resources?path={}'.format(quote('disk:/' + filename))
    headers = {
        'Authorization': 'OAuth {token}'.format(token=config.sw_bonuses_ydisk_token),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, None, headers)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        import_file = result.get('file', None)
        import_md5 = result.get('md5', None)
        modified = result.get('modified', None)
        if not import_file:
            log.error('No file')
            raise self.retry(countdown=600, max_retries=4)  # 10 minutes

        import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
        filepath = os.path.join(import_dir, filename)
        lastpath = os.path.join(import_dir, re.sub(r'(\..+$)', '_last\\1', filename))
        log.info("Update1C")
        log.info("modified: " + str(modified))
        if modified and os.path.isfile(lastpath):
            mdate = dateparse.parse_datetime(modified)
            fdate = timezone.make_aware(datetime.fromtimestamp(os.path.getmtime(lastpath)))
            log.info("diff: " + str(mdate) + " < " + str(fdate))
            if mdate < fdate:
                log.info('File is not modified since last update: {} < {}'.format(mdate, fdate))
                return None

        log.info('Getting file %s' % import_file)
        request = Request(import_file, None, headers)
        response = urlopen(request)
        result = response.read()
        md5 = hashlib.md5(result).hexdigest()
        if md5 != import_md5:
            log.error('MD5 checksums differ')
            raise self.retry(countdown=600, max_retries=4)  # 10 minutes

        f = open(filepath, 'wb')
        f.write(result)
        f.close()

        import1c.s(filename).apply_async(queue=self.request.delivery_info['routing_key'])
        return modified
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Диском')
        log.error(message)
        raise self.retry(countdown=600, max_retries=12, exc=e)  # 10 minutes
    return 0


class fragile(object):
    class Break(Exception):
        """Break out of the with statement"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value.__enter__()

    def __exit__(self, etype, value, traceback):
        error = self.value.__exit__(etype, value, traceback)
        if etype == self.Break:
            return True
        return error


@shared_task(name='shop.tasks.count_stocks', queue='import')
def count_stocks():
    """
    Counts the stock of the products whose stock is reset, as import1c() resets it for all of them. Otherwise
    the API counts it in the first requests that show the products, and writes them, which made these requests slow.
    A task of its own, as it takes a minute or so, and import1c() runs under a lock that expires.
    """
    for product in Product.objects.filter(num__lt=0).only('num'):
        product.instock  # counts and saves it


@shared_task(name='shop.tasks.import1c', time_limit=7200, retry_backoff=True)
@single_instance_task(1200)
def import1c(file):
    log.error('Import1C')
    enable_flag('1C_IMPORT_RUNNING')

    currencies = {}

    def get_currency(code):
        if code not in currencies:
            currencies[code] = Currency.objects.get(pk=code)
        return currencies[code]

    def preprocess_quantities(quantities, pi_pos, n1_pos):
        quantities = [float(q.replace('\xA0', '').replace(',', '.')) for q in quantities]
        if pi_pos >= 0 and n1_pos >= 0:
            quantities[n1_pos] = min(quantities[n1_pos], quantities[pi_pos])
        return quantities

    frozen_orders = Order.objects.filter(status=Order.STATUS_FROZEN)
    frozen_products = defaultdict(list)
    if frozen_orders.exists():
        for order in frozen_orders:
            for item in order.items.all():
                quantity = 0
                stock = Stock.objects.filter(supplier__count_in_stock=True, product=item.product)
                if stock.exists():
                    for s in stock:
                        quantity = quantity + s.quantity + s.correction
                if quantity <= 0:
                    frozen_products[item.product.id].append(order)

    log.info('Frozen products %s' % str(frozen_products.keys()))

    stocks = list(Stock.objects.filter(~Q(correction=0)).values_list('product', 'supplier', 'correction', 'reason'))
    corrected_stocks = defaultdict(dict)
    for s in stocks:
        corrected_stocks[s[0]][s[1]] = (s[2], s[3])

    import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
    filepath = os.path.join(import_dir, file)

    src_file = open(filepath, mode='rt')
    tmp_file = tempfile.TemporaryFile(mode='r+t')
    for line in src_file:
        tmp_file.write(line)
    src_file.close()
    tmp_file.seek(0)
    lastpath = os.path.join(import_dir, re.sub(r'(\..+$)', '_last\\1', file))
    penultpath = os.path.join(import_dir, re.sub(r'(\..+$)', '_penult\\1', file))
    if os.path.isfile(lastpath):
        os.rename(lastpath, penultpath)
    os.rename(filepath, lastpath)

    table_copy = tempfile.TemporaryFile(mode='r+t')

    imported = 0
    updated = 0
    errors = []
    products = set()
    updated_products = []
    orders = set()
    suppliers = []
    date_reg = re.compile(r"\d{1,2}\.\d{2}\.\d{4} \d{1,2}:\d{2}:\d{2}")
    date = None

    pi_pos = -1
    n1_pos = -1

    with fragile(tmp_file) as csvfile:  # https://stackoverflow.com/a/23665658
        line = csvfile.readline().strip()
        if line[0] == '\ufeff':
            line = line[1:]  # trim the BOM away
        if date_reg.match(line):
            date = line
        next(csvfile)
        line = csvfile.readline().strip()
        if line != '//Список складов':
            errors.append("Неправильный формат файла импорта (ожидался список складов)")
            raise fragile.Break
        for line in csvfile:
            line = line.strip()
            if line == '//Остатки':
                break
            name, code = line.split(';')
            try:
                supplier = Supplier.objects.get(code1c=code)
                if supplier.code == 'Промимпэкс':
                    pi_pos = len(suppliers)
                if supplier.code == 'H':
                    n1_pos = len(suppliers)
                suppliers.append(supplier)
            except ObjectDoesNotExist:
                errors.append("Неизвестный поставщик с кодом %s: %s" % (code, name))
                suppliers.append(None)
        if not suppliers:
            errors.append("Нет ни одного известного поставщика")
            raise fragile.Break
        csv_fields = ('article', 'sp_cur_price', 'sp_cur_code', 'ws_cur_price', 'ws_cur_code', 'cur_price', 'cur_code')
        records = csv.DictReader(csvfile, delimiter=';', fieldnames=csv_fields, restkey='suppliers')
        for line in records:
            imported = imported + 1
            try:
                product = Product.objects.only(
                    'forbid_ws_price_import',
                    'forbid_price_import',
                    'cur_code',
                    'cur_price'
                ).get(article=line['article'])
                if line['sp_cur_code'] != '0':
                    try:
                        sp_cur_price = float(line['sp_cur_price'].replace('\xA0', ''))
                        product.sp_cur_price = int(round(sp_cur_price))
                        product.sp_cur_code = get_currency(line['sp_cur_code'])
                    except ValueError:
                        errors.append("%s: цена СП" % line['article'])
                if line['ws_cur_code'] != '0' and not product.forbid_ws_price_import:
                    try:
                        ws_cur_price = float(line['ws_cur_price'].replace('\xA0', ''))
                        if ws_cur_price > 0:
                            product.ws_cur_price = Decimal(ws_cur_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
                        product.ws_cur_code = get_currency(line['ws_cur_code'])
                    except ValueError:
                        errors.append("%s: оптовая цена" % line['article'])
                if line['cur_code'] != '0' and not product.forbid_price_import:
                    try:
                        cur_price = float(line['cur_price'].replace('\xA0', ''))
                        if cur_price > 0 and product.cur_code.code == 643:
                            cur_price = Decimal(cur_price).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
                            if product.cur_price != cur_price:
                                updated_products.append(product.id)
                            product.cur_price = cur_price
                    except ValueError:
                        errors.append("%s: розничная цена" % line['article'])
                product.save()
                products.add(product.id)
                quantities = preprocess_quantities(line['suppliers'], pi_pos, n1_pos)
                for idx, quantity in enumerate(quantities):
                    if suppliers[idx] is None:
                        continue
                    try:
                        correction, reason = corrected_stocks.get(product.id, {}).get(suppliers[idx].id, (0, ''))
                        if (quantity or correction) and product.article != 'г66356':
                            table_copy.write('{}\t{}\t{}\t{}\t{}\n'.format(quantity, product.id, suppliers[idx].id, correction, reason))
                        try:
                            del corrected_stocks[product.id][suppliers[idx].id]
                            if not corrected_stocks[product.id]:
                                del corrected_stocks[product.id]
                        except KeyError:
                            pass
                        """
                        count = Stock.objects.filter(product=product, supplier=suppliers[idx]).update(quantity=quantity)
                        if count and quantity == 0.0:
                            s = Stock.objects.get(product=product, supplier=suppliers[idx])
                            if s.correction == 0.0:
                                s.delete()
                        if not count and quantity > 0.0:
                            s = Stock.objects.create(product=product, supplier=suppliers[idx], quantity=quantity)
                        """
                    except ValueError:
                        errors.append("%s: состояние складa" % line['article'])
                    except IndexError:
                        errors.append("%s: неправильное количество складов" % line['article'])
                updated = updated + 1
            except MultipleObjectsReturned:
                errors.append("%s: артикль не уникален" % line['article'])
            except ObjectDoesNotExist:
                # errors.append("%s: товар отсутствует" % line['article'])
                pass

        if updated_products:
            post_update_products.s(updated_products).delay()

        for product, stocks in corrected_stocks.items():
            for stock, (correction, reason) in stocks.items():
                table_copy.write('{}\t{}\t{}\t{}\t{}\n'.format(0, product, stock, correction, reason))
        table_copy.seek(0)
        with connection.cursor() as cursor:
            log.info('Start 1C_IMPORT_COPYING')
            enable_flag('1C_IMPORT_COPYING')
            cursor.execute("BEGIN")
            cursor.execute("DELETE FROM shop_stock")
            # cursor.execute("TRUNCATE TABLE shop_stock RESTART IDENTITY")
            log.info('Continue 1C_IMPORT_COPYING')
            cursor.copy_from(table_copy, 'shop_stock', columns=('quantity', 'product_id', 'supplier_id', 'correction', 'reason'))
            cursor.execute("COMMIT")
            disable_flag('1C_IMPORT_COPYING')
            log.info('Stop 1C_IMPORT_COPYING')
    table_copy.close()
    tmp_file.close()

    for product_id in products:
        product = Product.objects.only('num').get(pk=product_id)
        product.num = -1
        product.save()
        if product_id in frozen_products.keys() and product.instock > 0:
            orders.update(frozen_products[product_id])
        if product_id in frozen_products.keys():
            log.error('F %d %d' % (product.pk, product.instock))

    log.info('Frozen orders %s' % str(orders))

    disable_flag('1C_IMPORT_RUNNING')
    count_stocks.delay()
    msg_plain = render_to_string('mail/shop/import1c_result.txt',
                                 {'file': file, 'date': date, 'imported': imported, 'updated': updated, 'errors': errors,
                                  'orders': orders, 'opts': Order._meta})
    send_mail(
        'Импорт 1С из %s' % file,
        msg_plain,
        config.sw_email_from,
        get_default_site().profile.manager_emails.split(','),
    )

    return date
