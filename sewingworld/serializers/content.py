from rest_framework import serializers

from django.contrib.flatpages.models import FlatPage

from sewingworld.models import SiteProfile

from shop.models import Country, City, Store, StoreImage, ServiceCenter, News, Advert, SalesAction

from .common import NonNullModelSerializer


class CountrySerializer(NonNullModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'enabled')


class CitySerializer(NonNullModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = City
        fields = '__all__'  # TODO refactor


class StoreImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreImage
        exclude = ('id', 'store')


class StoreListSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)
    phones = serializers.SerializerMethodField()

    class Meta:
        model = Store
        exclude = ('site', 'supplier', 'enabled')

    def get_phones(self, obj) -> list[str] | None:
        if not obj.phone:
            return None
        phones = obj.phone.split(',')
        if obj.phone2:
            phones.append(obj.phone2)
        return [phone.strip() for phone in phones]


class StoreSerializer(StoreListSerializer):
    images = StoreImageSerializer(many=True)


class ServiceCenterSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = ServiceCenter
        exclude = ('enabled',)


class SalesActionSerializer(NonNullModelSerializer):
    class Meta:
        model = SalesAction
        exclude = ('active', 'show_in_list', 'order', 'sites')


class FlatPageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        fields = ('url', 'title')


class FlatPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        exclude = ('sites',)


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        exclude = ('sites', 'active')


class AdvertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advert
        exclude = ('sites', 'active')


class SiteProfileSerializer(NonNullModelSerializer):
    id = serializers.SerializerMethodField()
    url_prefix = serializers.SerializerMethodField()
    city = CitySerializer(read_only=True)

    class Meta:
        model = SiteProfile
        fields = ('id', 'url_prefix', 'title', 'description', 'city', 'phone', 'wholesale')

    def get_id(self, obj) -> int:
        return obj.site.pk

    def get_url_prefix(self, obj) -> str:
        return 'https://' + obj.site.domain
