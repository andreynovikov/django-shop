from haystack import indexes

from django.conf import settings

from .models import Category, Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        filters = {
            'enabled': True,
            'price__gt': 0,
            'categories__in': root.get_descendants(include_self=True)
        }
        return self.get_model().objects.filter(**filters).distinct()
