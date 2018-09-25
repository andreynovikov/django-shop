import autocomplete_light.shortcuts as al
from .models import ShopUser, Category, Product, SalesAction, Store

# This will generate a PersonAutocomplete class
al.register(ShopUser,
    # Just like in ModelAdmin.search_fields
    search_fields=['phone', 'name'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Пользователь?',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 2,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 8,
        # Enable modern-style widget !
        #'class': 'modern-style',
    },
)


class CategoryAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name','^slug']
    model = Category
    order_by = 'order'
    
    def choice_label(self, choice):
        return '/'.join([x['name'] for x in choice.get_ancestors(include_self=True).values()])

al.register(CategoryAutocomplete)


al.register(Product,
  search_fields=['article', 'code', 'partnumber', 'gtin', 'title'],
  attrs={
        'placeholder': 'Товар?',
        'data-autocomplete-minimum-characters': 2,
    },
    widget_attrs={
        'data-widget-maximum-values': 8,
    },
)


al.register(SalesAction,
  search_fields=['name', 'slug'],
  attrs={
        'placeholder': 'Акция?',
        'data-autocomplete-minimum-characters': 1,
    },
    widget_attrs={
        'data-widget-maximum-values': 8,
    },
)


al.register(Store,
  search_fields=['address', 'address2', 'city__name'],
  attrs={
        'placeholder': 'Магазин?',
        'data-autocomplete-minimum-characters': 2,
    },
    widget_attrs={
        'data-widget-maximum-values': 8,
    },
)
