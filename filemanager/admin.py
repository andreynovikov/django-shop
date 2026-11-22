import posixpath
import re
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path as url_path, reverse
from django.utils.translation import gettext as _, ngettext, pgettext

from .models import File
from .storage import FileExists, FileManagerError, clean_path, get_store, join
from .usage import find_usage

POPUP_VAR = '_popup'
TARGET_VAR = '_target'
TARGET_RE = re.compile(r'^[\w-]{1,200}$')
ORDER_VAR = 'o'
# Columns the files can be ordered by: the key, and whether the first click orders them descending
ORDERINGS = {
    'name': (lambda entry: entry.name.casefold(), False),
    'size': (lambda entry: entry.size, True),
    'modified': (lambda entry: entry.modified, True),
}


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """
    The file browser. It takes the place of the change list, and the add and change forms are not used.
    """
    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        perms['add'] = False  # files are added in the browser, there is no add form
        return perms

    def get_urls(self):
        info = self.opts.app_label, self.opts.model_name
        view = self.admin_site.admin_view
        return [
            url_path('', view(self.browse_view), name='%s_%s_changelist' % info),
            url_path('upload/', view(self.upload_view), name='%s_%s_upload' % info),
            url_path('mkdir/', view(self.mkdir_view), name='%s_%s_mkdir' % info),
            url_path('rename/', view(self.rename_view), name='%s_%s_rename' % info),
            url_path('delete/', view(self.delete_file_view), name='%s_%s_delete' % info),
            url_path('usage/', view(self.usage_view), name='%s_%s_usage' % info),
        ]

    # Requests

    def keep_params(self, request):
        """Parameters that every page of the browser keeps: the file picker's popup and the order of files."""
        data = request.POST if request.method == 'POST' else request.GET
        params = {}
        target = data.get(TARGET_VAR, '')
        if data.get(POPUP_VAR) and TARGET_RE.match(target):
            params.update({POPUP_VAR: '1', TARGET_VAR: target})
        order = data.get(ORDER_VAR, '')
        if order.lstrip('-') in ORDERINGS and order != 'name':
            params[ORDER_VAR] = order
        return params

    def get_order(self, request):
        """(column, descending)"""
        order = self.keep_params(request).get(ORDER_VAR, 'name')
        return order.lstrip('-'), order.startswith('-')

    def browse_url(self, request, folder='', **params):
        query = {'dir': folder} if folder else {}
        query.update(self.keep_params(request))
        query.update(params)
        query = {name: value for name, value in query.items() if value}
        url = reverse('%s:%s_%s_changelist' % (self.admin_site.name, self.opts.app_label, self.opts.model_name))
        return url + ('?' + urlencode(query) if query else '')

    def columns(self, request, folder):
        """The sortable columns of the file list, as the admin's change list shows them"""
        column, descending = self.get_order(request)
        result = []
        for name, label in (
            ('name', pgettext('file manager', 'Name')),
            ('size', pgettext('file manager', 'Size')),
            ('modified', pgettext('file manager', 'Modified')),
        ):
            sorted_ = name == column
            first_descending = ORDERINGS[name][1]
            toggle = ('' if descending else '-') + name if sorted_ else ('-' if first_descending else '') + name
            result.append({
                'name': name,
                'label': label,
                'sorted': sorted_,
                'ascending': sorted_ and not descending,
                'url': self.browse_url(request, folder, **{ORDER_VAR: '' if toggle == 'name' else toggle}),
            })
        return result

    def get_path(self, request, name='path'):
        data = request.POST if request.method == 'POST' else request.GET
        try:
            return clean_path(data.get(name))
        except FileManagerError:
            raise Http404()

    def context(self, request, title, folder, **extra):
        crumbs, parts = [], folder.split('/') if folder else []
        for index, name in enumerate(parts):
            crumbs.append((name, self.browse_url(request, '/'.join(parts[:index + 1]))))
        keep = self.keep_params(request)
        return {
            **self.admin_site.each_context(request),
            'opts': self.opts,
            'title': title,
            'folder': folder,
            'root_url': self.browse_url(request),
            'folder_url': self.browse_url(request, folder),
            'crumbs': crumbs,
            'is_popup': POPUP_VAR in keep,
            'keep_params': keep,
            'keep_query': urlencode(keep),
            **extra,
        }

    def render(self, request, template, context):
        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'admin/filemanager/%s.html' % template, context)

    # Views

    def browse_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        store = get_store()
        folder = self.get_path(request, 'dir')
        if folder and store.kind(folder) != 'dir':
            raise Http404()
        folders, files = store.list(folder)
        column, descending = self.get_order(request)
        files.sort(key=ORDERINGS[column][0], reverse=descending)
        if column == 'name' and descending:
            folders.reverse()  # folders have no size or time, and stay ordered by name otherwise
        context = self.context(
            request, folder or _('Files'), folder,
            folders=[(entry, store.is_protected(entry.path)) for entry in folders],
            files=files,
            parent_url=self.browse_url(request, posixpath.dirname(folder)) if folder else None,
            protected=store.is_protected(folder),
            can_add=not store.is_protected(folder) and self.has_add_permission(request),
            can_change=self.has_change_permission(request),
            can_delete=self.has_delete_permission(request),
            names=[entry.name for entry in folders + files],
            columns=self.columns(request, folder),
        )
        return self.render(request, 'browse', context)

    def upload_view(self, request):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        if not self.has_add_permission(request):
            raise PermissionDenied
        store = get_store()
        folder = self.get_path(request, 'dir')
        overwrite = request.POST.get('overwrite') == '1'
        if overwrite and not self.has_change_permission(request):
            raise PermissionDenied
        saved = 0
        for upload in request.FILES.getlist('files'):
            try:
                store.save(folder, upload.name, upload, overwrite=overwrite)
                saved += 1
            except FileExists as e:
                self.message_user(request, _('%(error)s Upload it again and allow replacing.') % {'error': e}, messages.ERROR)
            except FileManagerError as e:
                self.message_user(request, str(e), messages.ERROR)
        if saved:
            self.message_user(request, ngettext('%d file uploaded.', '%d files uploaded.', saved) % saved, messages.SUCCESS)
        return HttpResponseRedirect(self.browse_url(request, folder))

    def mkdir_view(self, request):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        if not self.has_add_permission(request):
            raise PermissionDenied
        folder = self.get_path(request, 'dir')
        try:
            folder = get_store().mkdir(folder, request.POST.get('name', '').strip())
        except FileManagerError as e:
            self.message_user(request, str(e), messages.ERROR)
        return HttpResponseRedirect(self.browse_url(request, folder))

    def rename_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied
        store = get_store()
        path = self.get_path(request)
        kind = store.kind(path) if path else None
        if not kind:
            raise Http404()
        error = None
        target = path
        if request.method == 'POST':
            try:
                target = clean_path(request.POST.get('target', '').strip())
                store.rename(path, target)
                self.message_user(request, _('“%(path)s” is now “%(target)s”.') % {'path': path, 'target': target}, messages.SUCCESS)
                return HttpResponseRedirect(self.browse_url(request, posixpath.dirname(target)))
            except FileManagerError as e:
                error = str(e)
                target = request.POST.get('target', '')
        context = self.context(
            request, _('Rename or move “%(name)s”') % {'name': posixpath.basename(path)}, posixpath.dirname(path),
            path=path, is_dir=kind == 'dir', target=target, error=error,
            usage=find_usage(path, kind == 'dir', self.admin_site),
        )
        return self.render(request, 'rename', context)

    def delete_file_view(self, request):
        if not self.has_delete_permission(request):
            raise PermissionDenied
        store = get_store()
        path = self.get_path(request)
        kind = store.kind(path) if path else None
        if not kind:
            raise Http404()
        folder = posixpath.dirname(path)
        if request.method == 'POST':
            try:
                store.delete(path)
                self.message_user(request, _('“%(path)s” deleted.') % {'path': path}, messages.SUCCESS)
            except FileManagerError as e:
                self.message_user(request, str(e), messages.ERROR)
            return HttpResponseRedirect(self.browse_url(request, folder))
        context = self.context(
            request, _('Delete “%(name)s”') % {'name': posixpath.basename(path)}, folder,
            path=path, is_dir=kind == 'dir', protected=store.is_protected(path),
            file_count=store.count_files(path) if kind == 'dir' else None,
            usage=find_usage(path, kind == 'dir', self.admin_site),
        )
        return self.render(request, 'delete', context)

    def usage_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        store = get_store()
        path = self.get_path(request)
        kind = store.kind(path) if path else None
        if not kind:
            raise Http404()
        context = self.context(
            request, _('Where “%(name)s” is used') % {'name': posixpath.basename(path)}, posixpath.dirname(path),
            path=path, is_dir=kind == 'dir', url=store.url(path) if kind == 'file' else store.url(join(path, '')),
            usage=find_usage(path, kind == 'dir', self.admin_site),
        )
        return self.render(request, 'usage', context)
