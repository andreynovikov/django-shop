from __future__ import unicode_literals

from django.db import models

from djconfig.models import Config
from spirit.category.models import Category
from spirit.user.models import UserProfile
from spirit.topic.models import Topic
from spirit.comment.flag.models import CommentFlag

from shop.models import Product


class DjConfig(Config):
    class Meta:
        proxy = True
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'


class SpiritCategory(Category):
    class Meta:
        proxy = True
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class SpiritUserProfile(UserProfile):
    class Meta:
        proxy = True
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователя'


class SpiritTopic(Topic):
    class Meta:
        proxy = True
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'


class SpiritCommentFlag(CommentFlag):
    class Meta:
        proxy = True
        verbose_name = 'Пометка'
        verbose_name_plural = 'Пометки'


class BassetUser(models.Model):
    id = models.CharField(primary_key=True, max_length=25)
    login = models.CharField(unique=True, max_length=100)
    passwd = models.CharField(max_length=20)
    otype = models.CharField(max_length=10, blank=True, null=True)
    fio = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=50)
    paddress = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    country = models.IntegerField(blank=True, null=True)
    city = models.IntegerField(blank=True, null=True)
    ocity = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    phoneaux = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=30, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    metro = models.CharField(max_length=30, blank=True, null=True)
    inn = models.CharField(max_length=25, blank=True, null=True)
    account = models.CharField(max_length=250, blank=True, null=True)
    okonh = models.CharField(max_length=25, blank=True, null=True)
    sendemail = models.IntegerField(blank=True, null=True)
    sendfax = models.IntegerField(blank=True, null=True)
    subscribe = models.IntegerField(blank=True, null=True)
    person = models.CharField(max_length=30, blank=True, null=True)
    shipping = models.CharField(max_length=25, blank=True, null=True)
    payment = models.CharField(max_length=25, blank=True, null=True)
    currency = models.IntegerField(blank=True, null=True)
    discount = models.FloatField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    accpay = models.IntegerField(blank=True, null=True)
    discountcard = models.CharField(max_length=30, blank=True, null=True)
    privilege = models.IntegerField(blank=True, null=True)
    splitorder = models.CharField(max_length=25, blank=True, null=True)
    sex = models.CharField(max_length=1, blank=True, null=True)
    etc = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=4, blank=True, null=True)
    penalty = models.IntegerField()
    ip = models.CharField(max_length=15, blank=True, null=True)
    regtime = models.DateTimeField(blank=True, null=True)
    admnote = models.TextField(blank=True, null=True)
    trnfio = models.CharField(max_length=100)
    rating = models.IntegerField()
    pubmail = models.CharField(max_length=100, blank=True, null=True)
    showemail = models.IntegerField()
    paddress2 = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
        verbose_name = 'basset user'
        verbose_name_plural = 'basset users'

    def __str__(self):
        return self.login


class Topic(models.Model):
    title = models.CharField(max_length=50)
    descr = models.TextField(blank=True, null=True)
    privacy = models.IntegerField()
    enabled = models.BooleanField()
    isopen = models.BooleanField()
    seq = models.IntegerField()
    support = models.BooleanField(blank=True, null=True)
    parentid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'topics'
        ordering = ['seq']
        unique_together = (('id', 'enabled'),)
        verbose_name = 'old topic'
        verbose_name_plural = 'old topics'

    def __str__(self):
        return self.title


class Thread(models.Model):
    topic = models.ForeignKey(Topic, db_column='topic', on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    isopen = models.BooleanField()
    archived = models.BooleanField()
    owner = models.ForeignKey(BassetUser, db_column='owner', on_delete=models.CASCADE)
    mtime = models.DateTimeField(blank=True, null=True)
    notify = models.BooleanField()
    slink = models.IntegerField(blank=True, null=True)
    ip = models.CharField(max_length=15, blank=True, null=True)
    enabled = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'threads'
        ordering = ['pk']
        verbose_name = 'old thread'
        verbose_name_plural = 'old threads'

    def __str__(self):
        return self.title


class Opinion(models.Model):
    tid = models.ForeignKey(Thread, db_column='tid', on_delete=models.CASCADE)
    author = models.ForeignKey(BassetUser, db_column='author', on_delete=models.CASCADE)
    text = models.TextField()
    post = models.DateTimeField()
    mode = models.IntegerField()
    ip = models.CharField(max_length=15, blank=True, null=True)
    rate = models.IntegerField()
    edited = models.BooleanField()
    rated = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'discuss'
        ordering = ['pk']
        verbose_name = 'old opinion'
        verbose_name_plural = 'old opinions'


class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    uid = models.ForeignKey(BassetUser, db_column='uid', on_delete=models.CASCADE)
    otime = models.IntegerField()
    delivery = models.CharField(max_length=30)
    payment = models.CharField(max_length=30)
    ccode = models.CharField(max_length=3)
    addon = models.FloatField()
    tax = models.FloatField()
    psum = models.FloatField()
    stat = models.IntegerField()
    udata = models.TextField()
    src = models.CharField(max_length=120, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=4, blank=True, null=True)
    shop_name = models.CharField(max_length=100, blank=True, null=True)
    deliveryinfo = models.TextField(blank=True, null=True)
    refusereason = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'
        verbose_name = 'basset order'
        verbose_name_plural = 'basset orders'

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    orid = models.ForeignKey(Order, db_column='orid', primary_key=True, on_delete=models.CASCADE, related_name='item')
    pid = models.ForeignKey(Product, db_column='pid', on_delete=models.CASCADE)
    pq = models.IntegerField()
    pprice = models.FloatField()
    pccode = models.CharField(max_length=3)
    ptax = models.FloatField()
    pdiscount = models.FloatField()
    partner = models.CharField(max_length=20, blank=True, null=True)
    pway = models.IntegerField(blank=True, null=True)
    prate = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orderdata'
        unique_together = (('orid', 'pid'),)


class OrderStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    aname = models.CharField(max_length=50)
    extern = models.IntegerField()
    color = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orderstatlist'
        ordering = ['pk']
