"""
The managed tree: paths, checks and file operations. The views touch files only through a store.

A path is relative to the storage root, with '/' between its parts, and '' is the root. Names are kept as
they are typed or uploaded, and are not passed through Storage.get_valid_name(), which would change the URL.
"""
import os
import posixpath
import shutil
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.utils.translation import gettext as _

IMAGE_EXTENSIONS = {'.avif', '.bmp', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.webp'}
VIDEO_EXTENSIONS = {'.m4v', '.mov', '.mp4', '.ogv', '.webm'}
UPLOAD_PREFIX = '.upload-'


class FileManagerError(Exception):
    """An operation that can't be done. The message is for the user."""


class FileExists(FileManagerError):
    pass


def clean_name(name):
    """
    Checks one part of a path. Names that start with a dot are refused: they are hidden from the browser, which
    also keeps '.' and '..' out.
    """
    if (not name or name.startswith('.') or '/' in name or '\\' in name or len(name.encode('utf-8', 'surrogatepass')) > 255
            or any(unicodedata.category(char) in ('Cc', 'Cs') for char in name)):
        raise FileManagerError(_('“%(name)s” is not a valid name.') % {'name': name})
    return name


def clean_path(path):
    """
    Checks a path from a request, and returns it without the slashes at its ends.
    """
    path = (path or '').strip('/')
    if not path:
        return ''
    return '/'.join(clean_name(part) for part in path.split('/'))


def join(folder, name):
    return posixpath.join(folder, name) if folder else name


def file_kind(name):
    extension = posixpath.splitext(name)[1].lower()
    if extension in IMAGE_EXTENSIONS:
        return 'image'
    if extension in VIDEO_EXTENSIONS:
        return 'video'
    return 'file'


@dataclass
class Entry:
    name: str
    path: str
    is_dir: bool
    url: str = ''
    size: int = None
    modified: datetime = None

    @property
    def kind(self):
        return 'folder' if self.is_dir else file_kind(self.name)


def get_store():
    storage = storages[getattr(settings, 'FILEMANAGER_STORAGE', 'default')]
    if isinstance(storage, FileSystemStorage):
        return FileSystemStore(storage, getattr(settings, 'FILEMANAGER_PROTECTED', ()))
    raise ImproperlyConfigured(
        f'filemanager supports FileSystemStorage only, {type(storage).__name__} needs a store in filemanager.storage'
    )


class FileSystemStore:
    """
    Files of a FileSystemStorage. Writes go through the storage, so its permission modes apply. A replaced file
    is written beside the old one and then renamed over it, so the URL never serves a partial file.
    """
    def __init__(self, storage, protected=()):
        self.storage = storage
        self.protected = [prefix.strip('/') for prefix in protected if prefix.strip('/')]

    def url(self, path):
        return self.storage.url(path)

    def is_protected(self, path):
        """Protected paths hold the files of model fields and are browsed only."""
        return any(path == prefix or path.startswith(prefix + '/') for prefix in self.protected)

    def check_writable(self, path):
        if not path:
            raise FileManagerError(_('The root folder can’t be changed.'))
        if self.is_protected(path):
            raise FileManagerError(
                _('“%(path)s” holds the files of the site’s records and can’t be changed here.') % {'path': path}
            )

    def _os_path(self, path):
        return self.storage.path(path)  # safe_join() refuses paths outside the root

    def kind(self, path):
        """'dir', 'file' or None"""
        full = self._os_path(path)
        if os.path.isdir(full):
            return 'dir'
        if os.path.lexists(full):
            return 'file'
        return None

    def _timestamp(self, timestamp):
        if settings.USE_TZ:
            return datetime.fromtimestamp(timestamp, timezone.utc)
        return datetime.fromtimestamp(timestamp)

    def list(self, folder):
        """
        Folders and files of a folder, sorted by name. Hidden names (with a leading dot), and names that aren't
        UTF-8 and so can't be put into a URL, are left out.
        """
        folders, files = [], []
        if folder == '' and not os.path.isdir(self.storage.location):
            return folders, files
        with os.scandir(self._os_path(folder)) as entries:
            for entry in entries:
                try:
                    clean_name(entry.name)
                    path = join(folder, entry.name)
                    if entry.is_dir():
                        folders.append(Entry(entry.name, path, True))
                    else:
                        stat = entry.stat()
                        files.append(Entry(entry.name, path, False, self.url(path), stat.st_size, self._timestamp(stat.st_mtime)))
                except (FileManagerError, OSError):
                    continue
        key = lambda entry: entry.name.casefold()  # noqa: E731
        return sorted(folders, key=key), sorted(files, key=key)

    def count_files(self, folder):
        return sum(len(files) for _, _, files in os.walk(self._os_path(folder)))

    def mkdir(self, folder, name):
        path = join(folder, clean_name(name))
        self.check_writable(path)
        if self.kind(folder) != 'dir':
            raise FileManagerError(_('Folder “%(path)s” doesn’t exist.') % {'path': folder or '/'})
        if self.kind(path):
            raise FileManagerError(_('“%(path)s” already exists.') % {'path': path})
        os.mkdir(self._os_path(path))
        if self.storage.directory_permissions_mode is not None:
            os.chmod(self._os_path(path), self.storage.directory_permissions_mode)
        return path

    def save(self, folder, name, content, overwrite=False):
        """
        Saves an uploaded file under its own name. An existing file is replaced only with overwrite, and raises
        FileExists without it.
        """
        path = join(folder, clean_name(name))
        self.check_writable(path)
        if self.kind(folder) != 'dir':
            raise FileManagerError(_('Folder “%(path)s” doesn’t exist.') % {'path': folder or '/'})
        kind = self.kind(path)
        if kind == 'dir':
            raise FileManagerError(_('There is a folder named “%(path)s”.') % {'path': path})
        if kind and not overwrite:
            raise FileExists(_('“%(path)s” already exists.') % {'path': path})
        temporary = self.storage.save(join(folder, UPLOAD_PREFIX + uuid.uuid4().hex), content)
        try:
            os.replace(self._os_path(temporary), self._os_path(path))
        except OSError:
            self.storage.delete(temporary)
            raise
        return path

    def rename(self, source, target):
        """Renames or moves a file or a folder. Missing folders of the target are made."""
        self.check_writable(source)
        self.check_writable(target)
        if not self.kind(source):
            raise FileManagerError(_('“%(path)s” doesn’t exist.') % {'path': source})
        if target == source:
            return target
        if target.startswith(source + '/'):
            raise FileManagerError(_('A folder can’t be moved into itself.'))
        if self.kind(target):
            raise FileManagerError(_('“%(path)s” already exists.') % {'path': target})
        parent = posixpath.dirname(target)
        if parent:
            if self.kind(parent) == 'file':
                raise FileManagerError(_('“%(path)s” is a file.') % {'path': parent})
            os.makedirs(self._os_path(parent), exist_ok=True)
        os.rename(self._os_path(source), self._os_path(target))
        return target

    def delete(self, path):
        """Deletes a file, or a folder with everything in it."""
        self.check_writable(path)
        full = self._os_path(path)
        if os.path.isdir(full) and not os.path.islink(full):
            shutil.rmtree(full)
        elif os.path.lexists(full):
            os.remove(full)
        else:
            raise FileManagerError(_('“%(path)s” doesn’t exist.') % {'path': path})
