from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from shop.models import Product, ProductRelation, Manufacturer, Supplier, Country, Currency, Category

import pprint

class Command(BaseCommand):
    help = 'Imports products from basset'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        # get discount values
        cursor.execute('SELECT id, value FROM discounts')
        rows = cursor.fetchall()
        discounts = dict()
        discounts[0] = 0
        for k,v in rows:
            discounts[k] = v
        # get manufacturer short names
        cursor.execute('SELECT id, code FROM manufacturers')
        rows = cursor.fetchall()
        manufacturers = dict()
        manufacturers[0] = 'undefined'
        for k,v in rows:
            manufacturers[k] = v
        # get currency rates
        #cursor.execute('SELECT c.code, c.rate FROM currency c INNER JOIN (SELECT code, MAX(tstamp) AS maxtstamp FROM currency '\
        #               'GROUP BY code) gc ON (c.code = gc.code AND c.tstamp = gc.maxtstamp) WHERE c.code != ""')
        #rows = cursor.fetchall()
        #currencies = dict()
        #for k,v in rows:
        #    currencies[int(k)] = v
        """ inverse rates because of tricky logic """
        #print(currencies)
        #dollar = currencies[Product.CURRENCY_RUBLE]
        #currencies[Product.CURRENCY_RUBLE] = currencies[Product.CURRENCY_DOLLAR]
        #currencies[Product.CURRENCY_DOLLAR] = dollar
        # cache dictionaries
        shop_manufacturers = Manufacturer.objects.all()
        bool(shop_manufacturers)
        currencies = Currency.objects.all()
        bool(currencies)
        # get products
        cursor.execute('SELECT * FROM products')
        num = 0
        missing_cats = set()
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            row = dict(zip(columns, row))
            product, created = Product.objects.get_or_create(pk=row['id'])
            if created:
                product.gtin = 0
            product.enabled = row['enabled'] == 1
            product.code = row['code']
            product.article = row['article'] or ''
            product.partnumber = row['partnumber'] or ''
            product.title = row['name']
            #if row['ccode'] =='' or int(row['ccode']) == 0:
            #    row['ccode'] = '810'
            #product.cur_code = currencies.get(pk=int(row['ccode']))
            if product.cur_price == 0:
                product.cur_price = round(row['price'] or 0)
                product.cur_code = currencies.get(pk=643)
            #product.price = product.cur_price * currencies[product.cur_code]
            product.pct_discount = discounts[row['discount']]
            product.max_discount = row['maxdiscount'] or 0
            #product.image_prefix = ''.join(['images/', manufacturers[row['manid']], '/', product.code])
            product.warranty = row['guarantee'] or ''
            product.extended_warranty = row['warranty'] or ''
            product.manufacturer_warranty = row['manufacturer_warranty'] or False

            product.swcode = row['swcode'] or ''
            #sname=varchar(250) not null
            product.runame = row['runame'] or ''
            product.sales_notes = row['sales_notes'] or ''
            product.available = row['nal'] or ''
            product.bid = row['bid'] or ''
            product.cbid = row['cbid'] or ''
            product.show_on_sw = row['show_on_sw'] or False
            product.gift = row['gift'] or False
            product.market = row['market'] or False
            #nabor=models.BooleanField('Набор', default=False)
            #print(row['id'],  " ", row['manid'])
            if int(row['manid']) == 0:
                row['manid'] = '49' # FIXME used number!!!!!!
            try:
                product.manufacturer = shop_manufacturers.get(pk=int(row['manid']))
            except Manufacturer.DoesNotExist:
                self.stdout.write("Django does not contain manufacturer with id %s" % row['manid'])
            if int(row['supid']) == 0:
                row['supid'] = '3'
            try:
                product.supplier = Supplier.objects.get(pk=int(row['supid']))
            except Supplier.DoesNotExist:
                self.stdout.write("Django does not contain supplier with id %s" % row['supid'])
            if int(row['counid']) == 0:
                row['counid'] = '1'
            product.country = Country.objects.get(pk=int(row['counid']))
            if row['enginecounid'] is None or int(row['enginecounid']) == 0:
                row['enginecounid'] = '1'
            product.developer_country = Country.objects.get(pk=int(row['enginecounid']))
            product.oprice = row['oprice'] or 0
            #fullprice=models.PositiveIntegerField('', default=0)
            #product.spprice = row['spprice'] or 0
            #tax=integer not null default 0 references taxes(id)
            product.isnew = row['isnew'] or False
            product.deshevle = row['deshevle'] or False
            product.recomended = row['recomended'] or False
            product.absent = row['off'] or False
            #ishot=models.BooleanField('', default=False)
            #newyear=models.BooleanField('', default=False)
            product.internetonly = row['internetonly'] or False
            product.present = row['present'] or ''
            product.coupon = row['sale'] or False
            product.not_for_sale = row['notsale'] or False
            #nodiscount=bool default 0
            product.firstpage = row['firstpage'] or False
            product.suspend = row['suspend'] or False
            #image=varchar(50)
            product.opinion = row['opinion'] or ''
            product.dimensions = row['measures'] or ''
            product.measure = row['measure'] or ''
            product.weight = row['weight'] or 0
            product.delivery = row['delivery'] or 0
            product.consultant_delivery_price = row['consultant_delivery_price'] or 0
            product.spec = row['spec'] or ''
            product.descr = row['descr'] or ''
            product.state = row['state'] or ''
            product.stitches = row['stitches'] or ''
            product.complect = row['complect'] or ''
            product.dealertxt = row['dealertxt'] or ''
            #product.num = row['num'] or 0
            #boleroid=integer not null default 0
            product.shortdescr = row['shortdescr'] or ''
            product.yandexdescr = row['yandexdescr'] or ''
            #onum=models.SmallIntegerField('Заказано у поставщика', default=0)
            #plimit=models.SmallIntegerField('Мин. запас', default=0)
            #mark=integer default 0 references mark(id)
            product.whatis = row['whatis'] or ''
            product.whatisit = row['whatisit'] or ''
            product.fabric_verylite = row['fabric_verylite'] or ''
            product.fabric_lite = row['fabric_lite'] or ''
            product.fabric_medium = row['fabric_medium'] or ''
            product.fabric_hard = row['fabric_hard'] or ''
            product.fabric_veryhard = row['fabric_veryhard'] or ''
            product.fabric_stretch = row['fabric_stretch'] or ''
            product.fabric_leather = row['fabric_leather'] or ''
            product.sm_shuttletype = row['sm_shuttletype'] or ''
            product.sm_stitchwidth = row['sm_stitchwidth'] or ''
            product.sm_stitchlenght = row['sm_stitchlenght'] or ''
            product.sm_stitchquantity = row['sm_stitchquantity'] or 0
            product.sm_buttonhole = row['sm_buttonhole'] or ''
            product.sm_dualtransporter = row['sm_dualtransporter'] or ''
            product.sm_platformlenght = row['sm_platformlenght'] or ''
            product.sm_freearm = row['sm_freearm'] or ''
            product.ov_freearm = row['ov_freearm'] or ''
            product.sm_feedwidth = row['sm_feedwidth'] or ''
            product.sm_footheight = row['sm_footheight'] or ''
            product.sm_constant = row['sm_constant'] or ''
            product.sm_speedcontrol = row['sm_speedcontrol'] or ''
            product.sm_needleupdown = row['sm_needleupdown'] or ''
            product.sm_threader = row['sm_threader'] or ''
            product.sm_spool = row['sm_spool'] or ''
            product.sm_presscontrol = row['sm_presscontrol'] or ''
            product.sm_power = row['sm_power'] or 0
            product.sm_light = row['sm_light'] or ''
            product.sm_organizersm_organizer = row['sm_organizer'] or ''
            product.sm_autostop = row['sm_autostop'] or ''
            product.sm_ruler = row['sm_ruler'] or ''
            product.sm_cover = row['sm_cover'] or ''
            product.sm_startstop = row['sm_startstop'] or ''
            product.sm_kneelift = row['sm_kneelift'] or ''
            product.sm_display = row['sm_display'] or ''
            product.sm_advisor = row['sm_advisor'] or ''
            product.sm_memory = row['sm_memory'] or ''
            product.sm_mirror = row['sm_mirror'] or ''
            product.sm_fix = row['sm_fix'] or ''
            product.sm_alphabet = row['sm_alphabet'] or ''
            product.sm_diffeed = row['sm_diffeed'] or ''
            product.sm_easythreading = row['sm_easythreading'] or ''
            product.sm_needles = row['sm_needles'] or ''
            product.sm_software = row['sm_software'] or ''
            product.sm_autocutter = row['sm_autocutter'] or ''
            product.sm_maxi = row['sm_maxi'] or ''
            product.sm_autobuttonhole_bool = row['sm_autobuttonhole_bool'] or False
            product.sm_threader_bool = row['sm_threader_bool'] or False
            product.sm_dualtransporter_bool = row['sm_dualtransporter_bool'] or False
            product.sm_alphabet_bool = row['sm_alphabet_bool'] or False
            product.sm_maxi_bool = row['sm_maxi_bool'] or False
            product.sm_patterncreation_bool = row['sm_patterncreation_bool'] or False
            product.sm_advisor_bool = row['sm_advisor_bool'] or False
            product.sw_datalink = row['sw_datalink'] or ''
            product.sw_hoopsize = row['sw_hoopsize'] or ''
            product.km_class = row['km_class'] or ''
            product.km_needles = row['km_needles'] or ''
            product.km_font = row['km_font'] or ''
            product.km_prog = row['km_prog'] or ''
            product.km_rapport = row['km_rapport'] or ''
            product.prom_transporter_type = row['prom_transporter_type'] or ''
            product.prom_shuttle_type = row['prom_shuttle_type'] or ''
            product.prom_speed = row['prom_speed'] or ''
            product.prom_needle_type = row['prom_needle_type'] or ''
            product.prom_stitch_lenght = row['prom_stitch_lenght'] or ''
            product.prom_foot_lift = row['prom_foot_lift'] or ''
            product.prom_fabric_type = row['prom_fabric_type'] or ''
            product.prom_oil_type = row['prom_oil_type'] or ''
            product.prom_weight = row['prom_weight'] or ''
            product.prom_cutting = row['prom_cutting'] or ''
            product.prom_threads_num = row['prom_threads_num'] or ''
            product.prom_power = row['prom_power'] or ''
            product.prom_bhlenght = row['prom_bhlenght'] or ''
            product.prom_overstitch_lenght = row['prom_overstitch_lenght'] or ''
            product.prom_overstitch_width = row['prom_overstitch_width'] or ''
            product.prom_stitch_width = row['prom_stitch_width'] or ''
            product.prom_needle_width = row['prom_needle_width'] or ''
            product.prom_needle_num = row['prom_needle_num'] or ''
            product.prom_platform_type = row['prom_platform_type'] or ''
            product.prom_button_diaouter = row['prom_button_diaouter'] or ''
            product.prom_button_diainner = row['prom_button_diainner'] or ''
            product.prom_needle_height = row['prom_needle_height'] or ''
            product.prom_stitch_type = row['prom_stitch_type'] or ''
            product.prom_autothread = row['prom_autothread'] or ''
            product.save()
            categories = list(product.categories.all())
            ccursor = connection.cursor()
            ccursor.execute("select cid from sj_cats where sid = %s and tab = 'products'", [row['id']])
            for crow in ccursor.fetchall():
                try:
                    category = Category.objects.get(basset_id=crow[0])
                    if category in categories:
                        categories.remove(category)
                    else:
                        product.categories.add(category)
                except Category.DoesNotExist:
                    if crow[0] not in missing_cats:
                        self.stdout.write("Django does not contain category with basset id %d" % crow[0])
                        missing_cats.add(crow[0])
            if categories:
                product.categories.remove(*categories)
            ccursor.close()
            num = num + 1
        self.stdout.write('Successfully imported %d product(s)' % num)
        # get product relations
        cursor.execute('SELECT * FROM om_links')
        num = 0
        ProductRelation.objects.all().delete()
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            row = dict(zip(columns, row))
            if not row['n1'] == 'products' or not row['n2'] == 'products':
                continue
            kind = None
            if row['type'] == 'default':
                kind = ProductRelation.KIND_ACCESSORY
            if row['type'] == 'illegal':
                kind = ProductRelation.KIND_SIMILAR
            if row['type'] == 'gift':
                kind = ProductRelation.KIND_GIFT
            if kind is None:
                continue
            try:
                parent = Product.objects.get(pk=int(row['i1']))
            except Product.DoesNotExist:
                self.stdout.write("Django does not contain product with id %s" % row['i1'])
                continue
            try:
                child = Product.objects.get(pk=int(row['i2']))
            except Product.DoesNotExist:
                self.stdout.write("Django does not contain product with id %s" % row['i2'])
                continue
            ProductRelation.objects.create(parent_product=parent, child_product=child,kind=kind)
            num = num + 1
        self.stdout.write('Successfully imported %d product relation(s)' % num)
        cursor.close()
