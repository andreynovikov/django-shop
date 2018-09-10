import re
import datetime
import logging

from decimal import Decimal, ROUND_UP, ROUND_HALF_EVEN

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.sites.models import Site
from django.db import connection, models
from django.db.models.signals import pre_save, post_save
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse

from colorfield.fields import ColorField

from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField

from tagging.fields import TagField

from model_utils import FieldTracker


logger = logging.getLogger(__name__)

WHOLESALE = getattr(settings, 'SHOP_WHOLESALE', False)


class ShopUserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError('Users must have a phone')

        user = self.model(phone=self.normalize_phone(phone),)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password):
        user = self.create_user(phone, password=password,)
        user.is_admin = True
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_phone(phone):
        phone = re.sub(r"[^0-9\+]", "", phone)
        if not phone.startswith("+"):
            phone = "+7" + phone
        return phone

    @staticmethod
    def format_phone(phone):
        m = re.match(r"(\+7)(\d{3})(\d{3})(\d{2})(\d{2})", phone)
        if not m:
            return phone
        return "{0} ({1}) {2}-{3}-{4}".format(*m.groups())


class ShopUser(AbstractBaseUser):
    phone = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    postcode = models.CharField('индекс', max_length=10, blank=True)
    city = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    is_active = models.BooleanField('активный', default=True)
    is_admin = models.BooleanField('админ', default=False)
    is_staff = models.BooleanField('сотрудник', default=False)
    is_wholesale = models.BooleanField('оптовик', default=False)
    tags = TagField('теги')

    objects = ShopUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    @staticmethod
    def autocomplete_search_fields():
        return ['id__iexact', 'name__icontains', 'phone__icontains', 'email__icontains']

    def get_short_name(self):
        return self.name or self.phone

    def get_full_name(self):
        return self.get_short_name()

    def __str__(self):
        return self.get_short_name()

    def related_label(self):
        if self.name:
            return "%s (%s)" % (self.name, self.phone)
        else:
            return self.phone

    def has_perm(self, perm, obj=None):
        #if self.is_active and self.is_superuser:
        #    return True
        if perm == 'wholesale':
            return self.is_wholesale
        return True

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    @staticmethod
    def has_module_perms(app_label):
        # Does the user have permissions to view the app `app_label`?
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_superuser(self):
        return self.is_admin


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    basset_id = models.PositiveSmallIntegerField('id в Бассет', null=True, blank=True)
    active = models.BooleanField()
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    image = models.ImageField('изображение', upload_to='categories', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    promo_image = models.ImageField('промо изображение', upload_to='categories', blank=True,
                              width_field='promo_image_width', height_field='promo_image_height')
    promo_image_width = models.IntegerField(null=True, blank=True)
    promo_image_height = models.IntegerField(null=True, blank=True)
    order = models.PositiveIntegerField()

    def get_active_descendants(self):
        return self.get_descendants().filter(active=True)

    def get_absolute_url(self):
        return reverse('category', kwargs={'path': self.get_path()})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    class MPTTMeta:
        order_insertion_by = ['order']


class Currency(models.Model):
    code = models.PositiveSmallIntegerField('код', primary_key=True)
    name = models.CharField('название', max_length=20)
    rate = models.DecimalField('курс', max_digits=5, decimal_places=2, default=1)

    class Meta:
        verbose_name = 'валюта'
        verbose_name_plural = 'валюты'

    def __str__(self):
        return self.name

def update_product_prices(sender, instance, **kwargs):
    products = Product.objects.filter(models.Q(cur_code=instance) | models.Q(ws_cur_code=instance))
    for product in products:
        product.save()

post_save.connect(update_product_prices, sender=Currency, dispatch_uid='update_product_prices')


class Country(models.Model):
    name = models.CharField('название', max_length=100)
    ename = models.CharField('англ. название', max_length=100)
    enabled = models.BooleanField('включена', default=True)

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    code = models.CharField('код', max_length=30)
    name = models.CharField('название', max_length=150)
    machinemaker = models.BooleanField('машины делает', default=False)
    accessorymaker = models.BooleanField('аксессуары делает', default=False)

    class Meta:
        verbose_name = 'производитель'
        verbose_name_plural = 'производители'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    code = models.CharField('код', max_length=10)
    name = models.CharField('название', max_length=100)
    show_in_order = models.BooleanField('показывать в заказе', default=False, db_index=True)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'

    @staticmethod
    def autocomplete_search_fields():
        return ['code__startswith', 'name__icontains']

    def __str__(self):
        return self.name


class Contractor(models.Model):
    code = models.CharField('код 1С', max_length=64)
    name = models.CharField('название', max_length=100)

    class Meta:
        verbose_name = 'контрагент'
        verbose_name_plural = 'контрагенты'

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField('идентификатор', max_length=20, unique=True, db_index=True)
    article = models.CharField('код 1С', max_length=20, blank=True, db_index=True)
    partnumber = models.CharField('partnumber', max_length=200, blank=True, db_index=True)
    gtin = models.CharField('GTIN', max_length=17, blank=True, db_index=True)
    enabled = models.BooleanField('включён', default=False, db_index=True)
    title = models.CharField('название', max_length=200)
    price = models.DecimalField('цена, руб', max_digits=10, decimal_places=2, default=0)
    cur_price = models.DecimalField('цена, вал', max_digits=10, decimal_places=2, default=0)
    cur_code = models.ForeignKey(Currency, verbose_name='валюта', related_name="rtprice", on_delete=models.PROTECT, default=643)
    ws_price =  models.DecimalField('опт. цена, руб', max_digits=10, decimal_places=2, default=0)
    ws_cur_price =  models.DecimalField('опт. цена, вал', max_digits=10, decimal_places=2, default=0)
    ws_cur_code = models.ForeignKey(Currency, verbose_name='опт. валюта', related_name="wsprice", on_delete=models.PROTECT, default=643)
    ws_pack_only = models.BooleanField('опт. только упаковкой', default=False)
    sp_price =  models.DecimalField('цена СП, руб', max_digits=10, decimal_places=2, default=0)
    sp_cur_price=models.DecimalField('цена СП, вал', max_digits=10, decimal_places=2, default=0)
    sp_cur_code = models.ForeignKey(Currency, verbose_name='СП валюта', related_name="spprice", on_delete=models.PROTECT, default=643)
    pct_discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    val_discount = models.DecimalField('скидка, руб', max_digits=6, decimal_places=2, default=0)
    ws_pct_discount = models.PositiveSmallIntegerField('опт. скидка, %', default=0)
    max_discount = models.PositiveSmallIntegerField('макс. скидка, %', default=10)
    ws_max_discount = models.PositiveSmallIntegerField('опт. макс. скидка, %', default=10)
    image_prefix = models.CharField('префикс изображения', max_length=200)
    categories = TreeManyToManyField('shop.Category', related_name='products',
                                     related_query_name='product', verbose_name='категории', blank=True)
    tags = TagField('теги')
    forbid_price_import = models.BooleanField('не импортировать цену', default=False)
    #number_inet = models.DecimalField('наличие в интернет-магазине', max_digits=10, decimal_places=2, default=0)
    #number_prol = models.DecimalField('наличие на пролетарке', max_digits=10, decimal_places=2, default=0)
    warranty = models.CharField('гарантия', max_length=20, blank=True)
    extended_warranty = models.CharField('расширенная гарантия', max_length=20, blank=True)
    manufacturer_warranty = models.BooleanField('официальная гарантия', default=False)

    swcode=models.CharField('Код товара в ШМ', max_length=20, blank=True)
    #todo delete: sname=varchar(250) not null
    runame=models.CharField('Русское название', max_length=200, blank=True)
    sales_notes=models.CharField('Yandex.Market Sales Notes', max_length=50, blank=True)
    #nal
    available=models.CharField('Наличие', max_length=255, blank=True)
    bid=models.CharField('Ставка маркета для основной выдачи', max_length=10, blank=True)
    cbid=models.CharField('Ставка маркета для карточки модели', max_length=10, blank=True)
    show_on_sw=models.BooleanField('Показать на основной витрине', default=True)
    gift=models.BooleanField('Годится в подарок', default=False)
    market=models.BooleanField('Выгружать в маркет', default=False)
    #todo refactor: nabor=models.BooleanField('Набор', default=False)
    #manid
    manufacturer=models.ForeignKey(Manufacturer, verbose_name="Производитель", on_delete=models.PROTECT, default=49)
    #supid
    #supplier=models.ForeignKey(Supplier, verbose_name="Поставщик", on_delete=models.PROTECT, default=4)
    #counid
    country=models.ForeignKey(Country, verbose_name="Страна-производитель", on_delete=models.PROTECT, default=1)
    #enginecounid
    developer_country=models.ForeignKey(Country, verbose_name="Страна-разработчик", on_delete=models.PROTECT, related_name="developed_product", default=1)
    oprice=models.DecimalField('Цена розничная', max_digits=10, decimal_places=2, default=0)
    #todo delete: fullprice=models.PositiveIntegerField('', default=0)
    """
    todo: delete
    tax=integer not null default 0 references taxes(id)
    """
    isnew=models.BooleanField('Новинка', default=False)
    deshevle=models.BooleanField('Нашли дешевле', default=False)
    recomended=models.BooleanField('Рекомендуем', default=False)
    #off
    absent=models.BooleanField('Нет в продаже', default=False)
    #todo add: ishot=models.BooleanField('', default=False)
    #todo delete: newyear=models.BooleanField('', default=False)
    internetonly=models.BooleanField('Только в интернет-магазине', default=False)
    present=models.CharField('Подарок к этому товару', max_length=255, blank=True)
    #sale
    coupon=models.BooleanField('Предлагать купон', default=False)
    #notsale
    not_for_sale=models.BooleanField('Не показывать кнопку заказа', default=False)
    #todo delete: nodiscount=bool default 0
    firstpage=models.BooleanField('Показать на первой странице', default=False)
    suspend=models.BooleanField('Готовится к выпуску', default=False)
    #image=varchar(50)
    opinion=models.CharField('Ссылка на обсуждение модели', max_length=255, blank=True)
    #measures
    dimensions=models.CharField('Размеры', max_length=255, blank=True)
    measure=models.CharField('Единицы', max_length=10, blank=True)
    weight=models.FloatField('Вес нетто', default=0)
    delivery=models.SmallIntegerField('Доставка', default=0)
    consultant_delivery_price=models.DecimalField('Стоимость доставки с консультантом', max_digits=6, decimal_places=2, default=0)
    spec=models.TextField('Подробное описание', blank=True)
    descr=models.TextField('Краткое описание', blank=True)
    state=models.TextField('Состояние', blank=True)
    stitches=models.TextField('Строчки', blank=True)
    complect=models.TextField('Комплектация', blank=True)
    dealertxt=models.TextField('Текст про официального дилера', blank=True)
    num=models.SmallIntegerField('В наличии', default=-1)
    num_correction=models.SmallIntegerField('Корректировка наличия', default=0)
    stock=models.ManyToManyField(Supplier, through='Stock')
    pack_factor=models.SmallIntegerField('Количество в упаковке', default=1)
    #todo delete: boleroid=integer not null default 0
    shortdescr=models.TextField('Характеристика', blank=True)
    yandexdescr=models.TextField('Описание для Яндекс.Маркет', blank=True)
    #todo delete: onum=models.SmallIntegerField('Заказано у поставщика', default=0)
    #todo delete: plimit=models.SmallIntegerField('Мин. запас', default=0)
    """
    todo: delete
    mark=integer default 0 references mark(id)
    """
    whatis=models.TextField('Что это такое', blank=True)
    whatisit=models.CharField('Что это такое, кратко', max_length=50, blank=True)
    fabric_verylite=models.CharField('Очень легкие ткани', max_length=50, blank=True)
    fabric_lite=models.CharField('Легкие ткани', max_length=50, blank=True)
    fabric_medium=models.CharField('Средние ткани', max_length=50, blank=True)
    fabric_hard=models.CharField('Тяжелые ткани', max_length=50, blank=True)
    fabric_veryhard=models.CharField('Очень тяжелые ткани', max_length=50, blank=True)
    fabric_stretch=models.CharField('Трикотаж', max_length=50, blank=True)
    fabric_leather=models.CharField('Кожа', max_length=50, blank=True)
    sm_shuttletype=models.CharField('Тип челнока', max_length=50, blank=True)
    sm_stitchwidth=models.CharField('Максимальная ширина строчки, мм', max_length=50, blank=True)
    sm_stitchlenght=models.CharField('Максимальная длина стежка, мм', max_length=50, blank=True)
    sm_stitchquantity=models.SmallIntegerField('Количество строчек', default=0)
    sm_buttonhole=models.CharField('Режим вымётывания петли', max_length=255, blank=True)
    sm_dualtransporter=models.CharField('Верхний транспортёр', max_length=50, blank=True)
    sm_platformlenght=models.CharField('Длина платформы, см', max_length=50, blank=True)
    sm_freearm=models.CharField('Размеры "свободного рукава" (длина/обхват), см', max_length=50, blank=True)
    ov_freearm=models.CharField('Cвободный рукав оверлока', max_length=255, blank=True)
    sm_feedwidth=models.CharField('Ширина гребёнки транспортера, мм', max_length=50, blank=True)
    sm_footheight=models.CharField('Величина зазора под лапкой (нормальный/двойной)', max_length=50, blank=True)
    sm_constant=models.CharField('Электронный стабилизатор усилия прокола', max_length=50, blank=True)
    sm_speedcontrol=models.CharField('Регулятор (ограничитель) скорости', max_length=50, blank=True)
    sm_needleupdown=models.CharField('Программируемая остановка иглы в верхнем/нижнем положении', max_length=50, blank=True)
    sm_threader=models.CharField('Нитевдеватель', max_length=50, blank=True)
    sm_spool=models.CharField('Горизонтальное расположение катушки', max_length=50, blank=True)
    sm_presscontrol=models.CharField('Регулятор давления лапки', max_length=50, blank=True)
    sm_power=models.FloatField('Потребляемая мощность, вт', default=0)
    sm_light=models.CharField('Тип освещения', max_length=50, blank=True)
    sm_organizer=models.CharField('Органайзер', max_length=50, blank=True)
    sm_autostop=models.CharField('Автостоп при намотке нитки на шпульку', max_length=50, blank=True)
    sm_ruler=models.CharField('Линейка на корпусе', max_length=50, blank=True)
    sm_cover=models.CharField('Чехол', max_length=50, blank=True)
    sm_startstop=models.CharField('Клавиша шитья без педали', max_length=255, blank=True)
    sm_kneelift=models.CharField('Коленный рычаг подъема лапки', max_length=255, blank=True)
    sm_display=models.TextField('Дисплей', blank=True)
    sm_advisor=models.CharField('Швейный советник', max_length=255, blank=True)
    sm_memory=models.CharField('Память', max_length=255, blank=True)
    sm_mirror=models.CharField('Зеркальное отображение образца строчки', max_length=255, blank=True)
    sm_fix=models.CharField('Закрепка', max_length=255, blank=True)
    sm_alphabet=models.CharField('Алфавит', max_length=255, blank=True)
    sm_diffeed=models.CharField('Дифференциальный транспортер', max_length=255, blank=True)
    sm_easythreading=models.CharField('Простая заправка петлителей', max_length=255, blank=True)
    sm_needles=models.CharField('Иглы', max_length=255, blank=True)
    sm_software=models.TextField('Возможности встроенного ПО', blank=True)
    sm_autocutter=models.CharField('Автоматический нитеобрезатель', max_length=255, blank=True)
    sm_maxi=models.CharField('Макси узоры', max_length=255, blank=True)
    sm_autobuttonhole_bool=models.BooleanField('Делает автоматически петлю', default=False)
    sm_threader_bool=models.BooleanField('Есть нитевдеватель', default=False)
    sm_dualtransporter_bool=models.BooleanField('Есть встроенный транспортер', default=False)
    sm_alphabet_bool=models.BooleanField('Есть алфавит', default=False)
    sm_maxi_bool=models.BooleanField('Есть макси-узоры', default=False)
    sm_patterncreation_bool=models.BooleanField('Есть функция создания строчек', default=False)
    sm_advisor_bool=models.BooleanField('Есть швейный советник', default=False)
    sw_datalink=models.CharField('Способ связи с компьютером', max_length=255, blank=True)
    sw_hoopsize=models.CharField('Размер пяльцев', max_length=255, blank=True)
    km_class=models.CharField('Класс вязальной машины', max_length=255, blank=True)
    km_needles=models.CharField('Количество игл', max_length=255, blank=True)
    km_font=models.CharField('Количество фонтур', max_length=255, blank=True)
    km_prog=models.CharField('Способ программирования', max_length=255, blank=True)
    km_rapport=models.CharField('Раппорт программируемого рисунка', max_length=255, blank=True)
    prom_transporter_type=models.CharField('Тип транспортера', max_length=255, blank=True)
    prom_shuttle_type=models.CharField('Тип челнока', max_length=255, blank=True)
    prom_speed=models.CharField('Максимальная скорость шитья', max_length=255, blank=True)
    prom_needle_type=models.CharField('Размер и тип иглы', max_length=255, blank=True)
    prom_stitch_lenght=models.CharField('Длина стежка', max_length=255, blank=True)
    prom_foot_lift=models.CharField('Высота подъема лапки', max_length=255, blank=True)
    prom_fabric_type=models.CharField('Тип материала', max_length=255, blank=True)
    prom_oil_type=models.CharField('Тип смазки', max_length=255, blank=True)
    prom_weight=models.CharField('Вес брутто', max_length=255, blank=True)
    prom_cutting=models.CharField('Обрезка нити', max_length=255, blank=True)
    prom_threads_num=models.CharField('Количество нитей', max_length=255, blank=True)
    prom_power=models.CharField('Мощность', max_length=255, blank=True)
    prom_bhlenght=models.CharField('Длина петли', max_length=255, blank=True)
    prom_overstitch_lenght=models.CharField('Максимальная длина обметочного стежка', max_length=255, blank=True)
    prom_overstitch_width=models.CharField('Максимальная ширина обметочного стежка', max_length=255, blank=True)
    prom_stitch_width=models.CharField('Ширина зигзагообразной строчки', max_length=255, blank=True)
    prom_needle_width=models.CharField('Расстояние между иглами', max_length=255, blank=True)
    prom_needle_num=models.CharField('Количество игл', max_length=255, blank=True)
    prom_platform_type=models.CharField('Тип платформы', max_length=255, blank=True)
    prom_button_diaouter=models.CharField('Наружный диаметр пуговицы', max_length=255, blank=True)
    prom_button_diainner=models.CharField('Внутренний диаметр пуговицы', max_length=255, blank=True)
    prom_needle_height=models.CharField('Ход игловодителя', max_length=255, blank=True)
    prom_stitch_type=models.CharField('Тип стежка', max_length=255, blank=True)
    prom_autothread=models.CharField('Автоматический нитеотводчик', max_length=255, blank=True)

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def save(self, *args, **kwargs):
        self.price = self.cur_price * self.cur_code.rate
        self.ws_price = self.ws_cur_price * self.ws_cur_code.rate
        self.sp_price = self.sp_cur_price * self.sp_cur_code.rate
        self.image_prefix = ''.join(['images/', self.manufacturer.code, '/', self.code])
        super(Product, self).save(*args, **kwargs)

    @property
    def cost(self):
        return self.price - self.discount

    @property
    def discount(self):
        pd = Decimal(0)
        if self.pct_discount > 0:
            price = self.price.quantize(Decimal('1'), rounding=ROUND_UP)
            pd = (price * Decimal(self.pct_discount / 100)).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        if self.val_discount > pd:
            pd = self.val_discount
        return pd

    @property
    def ws_cost(self):
        return self.ws_price - self.ws_discount

    @property
    def ws_discount(self):
        pd = Decimal(0)
        if self.ws_pct_discount > 0:
            return (self.ws_price * Decimal(self.ws_pct_discount / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        else:
            return Decimal(0)

    @property
    def instock(self):
        if self.num >= 0:
            return self.num

        self.num = 0
        suppliers = self.stock.filter(show_in_order=True)
        if suppliers.exists():
            for supplier in suppliers:
                stock = Stock.objects.get(product=self, supplier=supplier)
                self.num = self.num + stock.quantity
        cursor = connection.cursor()
        cursor.execute("""SELECT SUM(shop_orderitem.quantity) AS quantity FROM shop_orderitem
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
                          AND shop_orderitem.product_id = %s GROUP BY shop_orderitem.product_id""", (self.id,))
        if cursor.rowcount:
            row = cursor.fetchone()
            self.num = self.num - float(row[0])
        cursor.close()
        self.num = self.num + self.num_correction

        super(Product, self).save()

        return self.num

    @staticmethod
    def autocomplete_search_fields():
        return ['title__icontains', 'code__icontains', 'article__icontains', 'partnumber__icontains']

    def __str__(self):
        return " ".join([self.code, self.article, self.title])


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='item')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    quantity = models.FloatField('кол-во', default=0)

    class Meta:
        verbose_name = 'запас'
        verbose_name_plural = 'запасы'
        unique_together = ('product', 'supplier')


class Basket(models.Model):
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=30, blank=True)
    utm_source = models.CharField(max_length=20, blank=True)

    def product_cost(self, product):
        if WHOLESALE:
            return product.ws_price - self.product_discount(product)
        else:
            return product.price - self.product_discount(product)

    def product_pct_discount(self, product):
        """ Calculates maximum percent discount based on product, user and maximum discount """
        if WHOLESALE:
            pd = max(product.ws_pct_discount, self.user_discount)
            if pd > product.ws_max_discount:
                pd = product.ws_max_discount
            pdp = round(product.ws_price * (pd / 100))
            if pdp < product.sp_price:
                d = product.ws_price - product.sp_price
                pd = int(d / product.ws_price * 100)
        else:
            pd = max(product.pct_discount, self.user_discount)
            if pd > product.max_discount:
                pd = product.max_discount
        return pd

    def product_discount(self, product):
        pd = Decimal(0)
        pct = self.product_pct_discount(product)
        if pct > 0:
            if WHOLESALE:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
        if not WHOLESALE and product.val_discount > pd:
            pd = product.val_discount
        return pd

    def product_discount_text(self, product):
        """ Provides human readable discount string. """
        pd = Decimal(0)
        pdv = 0
        pdt = False
        pct = self.product_pct_discount(product)
        if pct > 0:
            if WHOLESALE:
                price = product.ws_price
                qnt = Decimal('0.01')
            else:
                price = product.price.quantize(Decimal('1'), rounding=ROUND_UP)
                qnt = Decimal('1')
            pd = (price * Decimal(pct / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            pdv = pct
            pdt = True
        if not WHOLESALE and product.val_discount > pd:
            pd = product.val_discount
            pdv = product.val_discount
            pdt = False
        if pd == 0:
            return ''
        pds = ' руб.'
        if pdt:
             pds = '%'
        return '%d%s' % (pdv, pds)

    @property
    def total(self):
        total = 0
        for item in self.items.all():
            total += item.price
        return total

    @property
    def quantity(self):
        quantity = 0
        for item in self.items.all():
            quantity += item.quantity
        return quantity

    @cached_property
    def user_discount(self):
        # if session contains valid user, get his discount
        session_data = self.session.get_decoded()
        discount = session_data.get('discount', 0)
        uid = session_data.get('_auth_user_id')
        try:
            user = ShopUser.objects.get(id=uid)
            if user.discount > discount:
                return user.discount
        except ShopUser.DoesNotExist:
            pass
        # if no user data available return session discount
        if not self.phone:
            return discount
        norm_phone = ShopUserManager.normalize_phone(self.phone)
        # if there is a user with such phone get his discount
        try:
            user = ShopUser.objects.get(phone=norm_phone)
            if user.discount > discount:
                return user.discount
        except ShopUser.DoesNotExist:
            pass
        return discount

    def update_session(self, session_key):
        if self.session_id != session_key:
            self.session_id = session_key
            self.save()

    def was_created_recently(self):
        return self.created >= timezone.now() - datetime.timedelta(days=1)
    was_created_recently.admin_order_field = 'created'
    was_created_recently.boolean = True
    was_created_recently.short_description = 'Created recently?'


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, related_name='items', related_query_name='item')
    product = models.ForeignKey(Product, related_name='+')
    quantity = models.PositiveSmallIntegerField(default=1)

    @property
    def price(self):
        if WHOLESALE:
            return (self.cost * Decimal(self.quantity)).quantize(Decimal('0.01'), rounding=ROUND_UP)
        else:
            return (self.cost * Decimal(self.quantity)) #.quantize(Decimal('1'), rounding=ROUND_UP)

    @property
    def cost(self):
        if WHOLESALE:
            return self.product.ws_price - self.discount
        else:
            return (self.product.price - self.discount).quantize(Decimal('1'), rounding=ROUND_UP)

    @property
    def discount(self):
        return self.basket.product_discount(self.product)

    @property
    def discount_text(self):
        """ Provides human readable discount string. """
        return self.basket.product_discount_text(self.product)


class Manager(models.Model):
    name = models.CharField('имя', max_length=100)
    color = ColorField(default='#000000')

    class Meta:
        verbose_name = 'менеджер'
        verbose_name_plural = 'менеджеры'

    def __str__(self):
        return self.name


class Courier(models.Model):
    name = models.CharField('имя', max_length=100)
    color = ColorField(default='#000000')

    class Meta:
        verbose_name = 'курьер'
        verbose_name_plural = 'курьеры'

    def __str__(self):
        return self.name


# may be switch to https://github.com/5monkeys/django-enumfield/
class Order(models.Model):
    PAYMENT_CASH = 1
    PAYMENT_CARD = 2
    PAYMENT_TRANSFER = 3
    PAYMENT_COD = 4
    PAYMENT_POS = 5
    PAYMENT_UNKNOWN = 99
    PAYMENT_CHOICES = (
        (PAYMENT_UNKNOWN, 'уточняется'),
        (PAYMENT_CASH, 'наличные'),
        (PAYMENT_CARD, 'банковская карта'),
        (PAYMENT_TRANSFER, 'банковский перевод'),
        (PAYMENT_COD, 'наложенный платёж'),
        (PAYMENT_POS, 'платёжный терминал'),
    )
    DELIVERY_COURIER = 1
    DELIVERY_CONSULTANT = 2
    DELIVERY_SELF = 3
    DELIVERY_TRANSPORT = 4
    DELIVERY_PICKPOINT = 5
    DELIVERY_YANDEX = 6
    DELIVERY_UNKNOWN = 99
    DELIVERY_CHOICES = (
        (DELIVERY_UNKNOWN, 'уточняется'),
        (DELIVERY_COURIER, 'курьер'),
        (DELIVERY_CONSULTANT, 'консультант'),
        (DELIVERY_SELF, 'получу сам в магазине'),
        (DELIVERY_TRANSPORT, 'транспортная компания'),
        (DELIVERY_PICKPOINT, 'PickPoint'),
        (DELIVERY_YANDEX, 'Яндекс.Доставка'),
    )
    STATUS_NEW = 0
    STATUS_ACCEPTED = 1
    STATUS_COLLECTING = 4
    STATUS_CANCELED = 8
    STATUS_FROZEN = 16
    STATUS_OTHERSHOP = 32
    STATUS_COLLECTED = 64
    STATUS_SERVICE = 128
    STATUS_DELIVERED_SHOP = 256
    STATUS_DELIVERED_STORE = 512
    STATUS_SENT = 1024
    STATUS_DELIVERED = 2048
    STATUS_CONSULTATION = 4096
    STATUS_PROBLEM = 8192
    STATUS_DONE = 16384
    STATUS_FINISHED = 0x0F000000
    STATUS_CHOICES = (
        (STATUS_NEW, 'новый заказ'),
        (STATUS_ACCEPTED, 'принят в работу'),
        (STATUS_COLLECTING, 'комплектуется'),
        (STATUS_CANCELED, 'отменен'),
        (STATUS_FROZEN, 'заморожен'),
        (STATUS_OTHERSHOP, 'передан в другой магазин'),
        (STATUS_COLLECTED, 'собран'),
        (STATUS_SERVICE, 'сервис'),
        (STATUS_SENT, 'доставляется'),
        (STATUS_DELIVERED, 'доставлен'),
        (STATUS_DELIVERED_SHOP, 'доставлен в магазин'),
        (STATUS_DELIVERED_STORE, 'передан в службу доставки'),
        (STATUS_CONSULTATION, 'консультация'),
        (STATUS_PROBLEM, 'проблема'),
        (STATUS_DONE, 'завершён'),
        (STATUS_FINISHED, 'выполнен'),
    )
    STATUS_COLORS = {
        STATUS_NEW: 'red',
        STATUS_ACCEPTED: 'orange',
        STATUS_COLLECTING: 'limegreen',
        STATUS_CANCELED: 'pink',
        STATUS_FROZEN: 'lightblue',
        STATUS_OTHERSHOP: 'gray',
        STATUS_COLLECTED: 'orange',
        STATUS_SERVICE: 'blue',
        STATUS_SENT: 'gray',
        STATUS_DELIVERED: 'darkgreen',
        STATUS_DELIVERED_SHOP: 'gray',
        STATUS_DELIVERED_STORE: 'gray',
        STATUS_CONSULTATION: 'darkgreen',
        STATUS_PROBLEM: 'black',
        STATUS_DONE: 'gray',
        STATUS_FINISHED: 'gray',
    }
    PICKPOINT_SERVICE_STD = 'STD'
    PICKPOINT_SERVICE_STDCOD = 'STDCOD'
    PICKPOINT_SERVICES = (
        (PICKPOINT_SERVICE_STD, 'предоплаченный товар'),
        (PICKPOINT_SERVICE_STDCOD, 'наложенный платеж'),
    )
    PICKPOINT_RECEPTION_CUR = 'CUR'
    PICKPOINT_RECEPTION_WIN = 'WIN'
    PICKPOINT_RECEPTIONS = (
        (PICKPOINT_RECEPTION_CUR, 'вызов курьера'),
        (PICKPOINT_RECEPTION_WIN, 'самопривоз'),
    )
    # order
    comment = models.TextField('комментарий', blank=True)
    shop_name = models.CharField('магазин', max_length=20, blank=True)
    site = models.ForeignKey(Site, verbose_name='сайт')
    payment = models.SmallIntegerField('оплата', choices=PAYMENT_CHOICES, default=PAYMENT_UNKNOWN)
    paid = models.BooleanField('оплачен', default=False)
    manager = models.ForeignKey(Manager, verbose_name='менеджер', blank=True, null=True)
    manager_comment = models.TextField('комментарий менеджера', blank=True)
    # delivery
    delivery = models.SmallIntegerField('доставка', choices=DELIVERY_CHOICES, default=DELIVERY_UNKNOWN, db_index=True)
    delivery_price = models.DecimalField('стоимость доставки', max_digits=8, decimal_places=2, default=0)
    delivery_info = models.TextField('ТК, ТТН, курьер', blank=True)
    delivery_tracking_number = models.CharField('трек-код', max_length=30, blank=True)
    delivery_date = models.DateField('дата доставки', blank=True, null=True)
    delivery_time_from = models.TimeField('от', blank=True, null=True)
    delivery_time_till = models.TimeField('до', blank=True, null=True)
    delivery_size_length = models.SmallIntegerField('длина', default=0)
    delivery_size_width = models.SmallIntegerField('ширина', default=0)
    delivery_size_height = models.SmallIntegerField('высота', default=0)
    delivery_yd_order = models.CharField('ЯД заказ', max_length=20, blank=True)
    delivery_pickpoint_terminal = models.CharField('терминал', max_length=10, blank=True)
    delivery_pickpoint_service = models.CharField('тип сдачи', max_length=10, choices=PICKPOINT_SERVICES, default=PICKPOINT_SERVICE_STD)
    delivery_pickpoint_reception = models.CharField('вид приема', max_length=10, choices=PICKPOINT_RECEPTIONS, default=PICKPOINT_RECEPTION_CUR)
    buyer = models.ForeignKey(Contractor, verbose_name='покупатель 1С', related_name='покупатель', blank=True, null=True)
    seller = models.ForeignKey(Contractor, verbose_name='продавец 1С', related_name='продавец', blank=True, null=True)
    wiring_date = models.DateField('дата проводки', blank=True, null=True)
    courier = models.ForeignKey(Courier, verbose_name='курьер', blank=True, null=True)
    store = models.ForeignKey(Store, verbose_name='магазин самовывоза', blank=True, null=True, on_delete=models.PROTECT)
    utm_source = models.CharField(max_length=20, blank=True)
    # user
    user = models.ForeignKey(ShopUser, verbose_name='покупатель')
    name = models.CharField('имя', max_length=100, blank=True)
    postcode = models.CharField('индекс', max_length=10, blank=True)
    city = models.CharField('город', max_length=255, blank=True)
    address = models.CharField('адрес', max_length=255, blank=True)
    phone = models.CharField('телефон', max_length=30, blank=True)
    phone_aux = models.CharField('доп.телефон', max_length=30, blank=True)
    email = models.EmailField('эл.почта', blank=True)
    is_firm = models.BooleanField('юр.лицо', default=False)
    firm_name = models.CharField('название организации', max_length=255, blank=True)
    firm_address = models.CharField('Юр.адрес', max_length=255, blank=True)
    firm_details = models.TextField('реквизиты', blank=True)
    # state
    created = models.DateTimeField('создан', auto_now_add=True)
    status = models.PositiveIntegerField('статус', choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)

    tracker = FieldTracker(fields=['status'])

    @property
    def total(self):
        return self.products_price + self.delivery_price

    @property
    def products_price(self):
        total = 0
        for item in self.items.all():
            total += item.price
        return total

    @property
    def products_quantity(self):
        quantity = 0
        for item in self.items.all():
            quantity += item.quantity
        return quantity

    @staticmethod
    def register(basket):
        session_data = basket.session.get_decoded()
        uid = session_data.get('_auth_user_id')
        user = ShopUser.objects.get(id=uid)
        order = Order.objects.create(user=user, site=Site.objects.get_current())
        order.utm_source = basket.utm_source
        if order.utm_source == 'yamarket':
            order.site = Site.objects.get(domain='market.yandex.ru')
        order.name = user.name
        order.postcode = user.postcode
        order.city = user.city
        order.address = user.address
        order.phone = user.phone
        order.email = user.email
        if WHOLESALE:
            qnt = Decimal('0.01')
        else:
            qnt = Decimal('1')
        for item in basket.items.all():
            # TODO Check compatibility with other shops
            if WHOLESALE:
                order.items.create(product=item.product,
                                   product_price=item.product.price.quantize(qnt, rounding=ROUND_UP),
                                   val_discount=item.discount,
                                   quantity=item.quantity)
            else:
                order.items.create(product=item.product,
                                   product_price=item.product.price.quantize(qnt, rounding=ROUND_UP),
                                   pct_discount=item.pct_discount,
                                   val_discount=item.product.val_discount,
                                   quantity=item.quantity)
        return order

    def append_user_tags(self, tags):
        user_tags = self.user.tags.split(',')
        merged = list(set(tags + user_tags))
        self.user.tags = ','.join(merged)
        self.user.save()

    def __str__(self):
        return "%s от %s" % (self.id, date_format(timezone.localtime(self.created), "DATETIME_FORMAT"))

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', related_query_name='item')
    product = models.ForeignKey(Product, related_name='+', verbose_name='товар')
    product_price = models.DecimalField('цена товара', max_digits=10, decimal_places=2, default=0)
    pct_discount = models.PositiveSmallIntegerField('скидка, %', default=0)
    val_discount = models.DecimalField('скидка, руб', max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveSmallIntegerField('количество', default=1)

    @property
    def price(self):
        return (self.product_price - self.discount) * self.quantity

    @property
    def cost(self):
        return self.product_price - self.discount

    @property
    def discount(self):
        pd = Decimal(0)
        if self.pct_discount > 0:
            price = self.product_price
            if WHOLESALE:
                qnt = Decimal('0.01')
            else:
                qnt = Decimal('1')
            pd = (price * Decimal(self.pct_discount / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
        if self.val_discount > pd:
            pd = self.val_discount
        return pd

    @property
    def discount_text(self):
        """ Provides human readable discount string. """
        pd = Decimal(0)
        pdv = 0
        pdt = False
        if self.pct_discount > 0:
            price = self.product_price
            if WHOLESALE:
                qnt = Decimal('0.01')
            else:
                qnt = Decimal('1')
            pd = (price * Decimal(self.pct_discount / 100)).quantize(qnt, rounding=ROUND_HALF_EVEN)
            pdv = self.pct_discount
            pdt = True
        if self.val_discount > pd:
            pd = self.val_discount
            pdv = self.val_discount
            pdt = False
        if pd == 0:
            return ''
        pds = ' руб.'
        if pdt:
             pds = '%'
        return '%d%s' % (pdv, pds)

    def __str__(self):
        return "%s, %d шт." % (self.product.title, self.quantity)

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'


def set_order_item_price(sender, instance, **kwargs):
    if instance._state.adding is True:
        if not instance.product_price:
            instance.product_price = instance.product.price

pre_save.connect(set_order_item_price, sender=OrderItem, dispatch_uid="set_order_item_price")
