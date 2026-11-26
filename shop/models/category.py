from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

__all__ = ['Category']


class Category(MPTTModel):
    name = models.CharField('заголовок', max_length=100)
    subname = models.CharField('подзаголовок', max_length=255, blank=True)
    slug = models.CharField(max_length=100, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.PROTECT)
    active = models.BooleanField('включена', default=True, db_index=True)
    hidden = models.BooleanField('спрятана', default=False, db_index=True)
    feed = models.BooleanField('выдавать в фиды', default=True)
    # Comma-separated names of the filters its page shows, see category_filters() in sewingworld/filters.py
    filters = models.CharField('фильтры', max_length=255, blank=True)
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    svg_icon = models.TextField('SVG иконка', blank=True)
    image = models.ImageField('изображение', upload_to='categories', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    promo_image = models.ImageField('промо изображение', upload_to='categories', blank=True,
                                    width_field='promo_image_width', height_field='promo_image_height')
    promo_image_width = models.IntegerField(null=True, blank=True)
    promo_image_height = models.IntegerField(null=True, blank=True)
    product_order = models.CharField('поле сортировки товаров', max_length=50, default='-cost')

    def get_api_path(self):
        # TODO: refactor: remove mptt_urls get_path injection, use this instead
        return '/'.join([item.slug for item in self.get_ancestors(include_self=True)[1:]])  # exclude root category

    def get_active_children(self):
        return self.get_children().filter(active=True, hidden=False)

    def get_active_descendants(self):
        return self.get_descendants().filter(active=True, hidden=False)

    def __str__(self):
        return self.name

    @classmethod
    def paths(cls):
        """
        The full path of each category, such as 'Каталог/Машины/Janome', by its ID in tree order. The admin labels
        categories with them, which tells those of the same name apart. One query reads them all.
        """
        categories = {category.pk: category for category in cls._default_manager.only('id', 'name', 'parent_id')}
        paths = {}
        for pk, category in categories.items():
            names = []
            while category is not None:
                names.append(category.name)
                category = categories.get(category.parent_id)
            paths[pk] = '/'.join(reversed(names))
        return paths

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
