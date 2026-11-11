from django.db.models import Sum, F, Q, OuterRef, Subquery

from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from shop.models import Product, Stock, Integration, ProductIntegration

from sewingworld.serializers.integrations import StockSerializer, IntegrationSerializer, IntegrationProductSerializer

from .common import StandardResultsSetPagination


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockSerializer
    pagination_class = StandardResultsSetPagination
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        queryset = Stock.objects.order_by('id')  # pages of an unordered query may repeat or skip rows
        suppliers = self.request.query_params.getlist('supplier')
        if len(suppliers) > 0:
            queryset = queryset.filter(supplier__code__in=suppliers)
        products = self.request.query_params.getlist('product')
        if len(products) > 0:
            queryset = queryset.filter(product__code__in=products)
        return queryset.distinct()


class IntegrationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [DjangoModelPermissions]

    @action(detail=True)
    def byutm(self, request, pk=None):
        integration = self.get_queryset().filter(utm_source=pk).first()
        if integration is None:
            raise NotFound()
        return Response(self.get_serializer(integration, context=self.get_serializer_context()).data)

    @action(detail=True)
    def products(self, request, pk=None):
        integration = self.get_object()

        filters = {
            'enabled': True,
            'price__gt': 0,
            'variations__exact': ''
        }

        if not integration.output_skip_categories:
            root_category = None
            if hasattr(integration.site, 'profile'):
                root_category = integration.site.profile.root_category
            if root_category is None:
                root_category = self.request.site.profile.root_category
            filters['categories__in'] = root_category.get_descendants(include_self=True).filter(active=True, feed=True)

        products = Product.objects.order_by().filter(**filters).distinct()

        if not integration.output_all:
            products = products.filter(
                integration=integration
            ).annotate(
                integration_price=Subquery(
                    ProductIntegration.objects.filter(
                        product=OuterRef('id'),
                        integration=integration
                    ).values('price')
                )
            )

        if integration.output_with_images:
            products = products.exclude(image__isnull=True).exclude(image__exact='')

        if integration.output_available:
            products = products.annotate(
                quantity=Sum('stock_item__quantity', filter=Q(stock_item__supplier__integration=integration)),
                correction=Sum('stock_item__correction', filter=Q(stock_item__supplier__integration=integration)),
                available=F('quantity') + F('correction')
            ).filter(available__gt=0)

        context = self.get_serializer_context()
        context['integration'] = integration
        return Response(IntegrationProductSerializer(IntegrationProductSerializer.prefetch(products), many=True, context=context).data)
