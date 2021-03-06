# coding: utf-8
from django.utils.module_loading import import_string

def _load(module):
    return import_string(module) if isinstance(module, str) else module

class view():
    def __init__(self, model, view, slug_field, root=None):
        def get_path(instance):
            path = '/'.join([getattr(item, slug_field) for item in instance.get_ancestors(include_self=True)]) + '/'
            if len(root) and path.startswith(root):
                return path[(len(root)+1):]
            return path

        self.model = _load(model)
        self.view = _load(view)
        self.slug_field = slug_field
        self.root = root

        # define 'get_path' method for model
        self.model.get_path = get_path
        #lambda instance, root='': '/'.join([getattr(item, slug_field) for item in instance.get_ancestors(include_self=True)]) + '/'

    def __call__(self, *args, **kwargs):
        if 'path' not in kwargs:
            raise ValueError('Path was not captured! Please capture it in your urlconf. Example: url(r\'^gallery/(?P<path>.*)\', mptt_urls.view(...), ...)')

        instance = None  # actual instance the path is pointing to (None by default)
        path = kwargs['path']
        try:
            instance_slug = path.split('/')[-2]  # slug of the instance
        except IndexError:
            instance_slug = None

        if instance_slug:
            candidates = self.model.objects.filter(**{self.slug_field: instance_slug})  # candidates to be the instance
            for candidate in candidates:
                # here we compare each candidate's path to the path passed to this view
                if candidate.get_path() == path:
                    if self.root and self.root != getattr(candidate.get_family()[0], self.slug_field):
                        continue
                    instance = candidate
                    break

        kwargs['instance'] = instance
        return self.view(*args, **kwargs)
