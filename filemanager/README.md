# filemanager

A file browser in the Django admin for the files that pages link to by URL: images, videos and documents in HTML text. It works like a file system. Folders nest freely, files keep the names they are uploaded with, and replacing a file keeps its URL. Files have no versions.

## Features

- **Browsing.** A folder at a time, with its folders and files, sizes and modification times. Hidden names (with a leading dot) and names that aren't UTF-8 are not shown. Files can be sorted by name, size or modification time, and the order stays while you move between folders.
- **Translations of labels.** Short labels such as "Delete" have the context `file manager`, so that the catalogs of apps installed earlier, which take precedence, don't replace them.
- **Uploading.** Several files at a time, by dropping them on the page or choosing them. A file whose name exists is replaced only after the browser asks. The new content is written beside the old file and renamed over it, so its URL never serves a partial file.
- **Folders.** Making, renaming, moving and deleting folders. Deleting a folder deletes everything in it, after a confirmation that says how many files it holds.
- **Renaming and moving** files and folders. The new path is typed from the root, and missing folders are made.
- **Where used.** Lists the records that link to a file or to the files of a folder. The rename and delete pages show it before anything changes. See [Where used](#where-used).
- **Protected folders.** Folders that hold the files of model fields (`FileField`, `ImageField`) can be browsed and linked from, but not changed.
- **HTML widget.** A text area for HTML fields that grows with its text, with an "Insert file" button that opens the browser in a popup. The chosen file goes into the text at the cursor: `<img>` for images, `<video controls>` for videos and `<a>` for other files.
- **Permissions:** the model permissions of `filemanager.File`:
  - view: browse, copy URLs, see where a file is used;
  - add: upload new files and make folders;
  - change: replace, rename and move;
  - delete: delete.
- **Translations:** English and Russian.

## Requirements

- Python 3.11 or later.
- Django 5.1 or later, tested with Django 6.1.
- A `FileSystemStorage`. Another storage, such as S3, needs a store class in `storage.py`, see [Other storages](#other-storages).

## Installation

1. Add `'filemanager'` to `INSTALLED_APPS`.
2. Run `python manage.py migrate filemanager`. The model has no table, but the migration creates its permissions.
3. Give the `HTMLTextarea` widget to the fields that hold HTML, see [The HTML widget](#the-html-widget).

The browser is at the changelist URL of `filemanager.File`, `admin:filemanager_file_changelist`.

## The HTML widget

`filemanager.widgets.HTMLTextarea` is an admin text area for HTML. It grows with its text, also in collapsed fieldsets and in inline rows added later. A `max-height` in its style still applies, and the text area scrolls beyond it. Its "Insert file" button opens the browser in a popup.

```python
from filemanager.widgets import HTMLTextarea

class PageAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'content': HTMLTextarea(attrs={'rows': 10, 'style': 'width: 95%; max-height: 500px'}),
        }
```

`admin_site` names the admin site whose browser the button opens, `'admin'` by default. The button is left out where that site's URLs aren't installed. The widget doesn't know the user, so users without file permissions see the button too. The browser then refuses them.

## Settings

| Setting | Default | |
|---|---|---|
| `FILEMANAGER_STORAGE` | `'default'` | The alias in `STORAGES` of the storage whose files are managed. |
| `FILEMANAGER_PROTECTED` | `[]` | Paths from the root, such as `'products'`, that are read-only together with everything below them. List the `upload_to` folders of your file fields. |
| `FILEMANAGER_USAGE_EXCLUDE` | `[]` | App labels (`'django_celery_results'`) or models (`'shop.Order'`) that "where used" doesn't search. |

## Where used

The text fields (`TextField`) of every model registered in the admin site are searched for `/` followed by the path, as stored and as it appears in a URL (`a b.jpg` and `a%20b.jpg`). That finds `/media/images/a.jpg`, `https://example.com/media/images/a.jpg` and aliases that keep the end of the path, such as `/images/a.jpg`. A short path at the root can also match a longer one: `/a.jpg` matches `/images/a.jpg`. Each search scans the tables, which is fine for pages opened one at a time. Exclude big tables that hold no links.

Rename and move don't change the links. The rename page lists the records to fix.

## Caching

Replacing a file keeps its URL, so the URL mustn't be cached for long. Serve the files with a short `max-age`, and with `ETag` or `Last-Modified` so that clients can revalidate. An image cache in front of the files, such as Next.js image optimization, keeps old copies for its own TTL.

## Other storages

The views use a store returned by `storage.get_store()`, and `FileSystemStore` is the only one so far. A store for an object storage implements the same methods. Folders are key prefixes there, so renaming one means copying and deleting each object under it, and an empty folder needs a placeholder object. Its `save()` puts the object under its final key, which replaces it in one step.

## Tests

```sh
python manage.py test filemanager                                  # in a project
python -m django test filemanager --settings=filemanager.tests.settings  # standalone, on SQLite
```
