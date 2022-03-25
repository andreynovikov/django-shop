from tqdm import tqdm
from django.core.management.base import BaseCommand
from shop.models import Order, Product, ProductIntegration, Integration


class Command(BaseCommand):
    help = 'Migrate integration data'

    def handle(self, *args, **options):
        product_num = 0
        order_num = 0

        """
        ProductIntegration.objects.all().delete()

        beru = Integration.objects.get(utm_source='beru')
        taxi = Integration.objects.get(utm_source='taxi')
        tax2 = Integration.objects.get(utm_source='tax2')
        tax3 = Integration.objects.get(utm_source='tax3')
        mdbs = Integration.objects.get(utm_source='mdbs')
        sber = Integration.objects.get(utm_source='sber')
        avito = Integration.objects.get(utm_source='avito')
        ali = Integration.objects.get(utm_source='ali')
        google = Integration.objects.get(utm_source='google')

        products = Product.objects.all()
        progress = tqdm(total=products.count(), desc="Products")
        for product in products:
            changed = False
            if product.beru:
                ProductIntegration(product=product, integration=beru, price=product.beru_price).save()
                changed = True
            if product.taxi:
                ProductIntegration(product=product, integration=taxi, price=product.beru_price).save()
                changed = True
            if product.tax2:
                ProductIntegration(product=product, integration=tax2, price=product.beru_price).save()
                changed = True
            if product.tax3:
                ProductIntegration(product=product, integration=tax3, price=product.beru_price).save()
                changed = True
            if product.mdbs:
                ProductIntegration(product=product, integration=mdbs, price=product.beru_price).save()
                changed = True
            if product.sber:
                ProductIntegration(product=product, integration=sber, price=product.sber_price).save()
                changed = True
            if product.avito:
                ProductIntegration(product=product, integration=avito, price=product.avito_price).save()
                changed = True
            if product.ali:
                ProductIntegration(product=product, integration=ali, price=product.ali_price).save()
                changed = True
            if product.merchant:
                ProductIntegration(product=product, integration=google).save()
                changed = True

            progress.update()
            if changed:
                product_num = product_num + 1

        progress.close()
        """

        Order.objects.all().update(integration=None)

        for integration in Integration.objects.filter(uses_api=True):
            orders = Order.objects.filter(site=integration.site)
            progress = tqdm(total=orders.count(), desc=integration.name)
            for order in orders:
                order.integration = integration
                order.save()
                progress.update()
                order_num = order_num + 1
            progress.close()

        self.stdout.write('Successfully migrated %d products and %d orders' % (product_num, order_num))
