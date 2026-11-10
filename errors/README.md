# errors

Server errors of a Django site, grouped and triaged in the Django admin.

`errors` collects every response with a 5xx status and every Celery task that fails. It groups repeats of the same error, so the admin shows one row per problem instead of one per occurrence. Each row has its occurrence count, frequency and a severity that administrators set. The app has no URLs or API of its own; it is visible only in the Django admin.

## Features

- **Collection.** One middleware records each response with a 5xx status:
  - exceptions raised in views or in other middleware;
  - 5xx responses that had no exception, such as a Django REST framework `APIException` or a view returning 503.

  When Celery is installed, tasks that fail for good are recorded too. Retries are not counted.
- **Grouping.** Occurrences belong to one error when all of these match:
  - the exception class;
  - the source: the HTTP method with the URL name (`GET product-detail`), or the task name;
  - the place in your code: the innermost frame outside the standard library and installed packages, by file and function, without the line number.

  Messages, parameters, line numbers and the rest of the stack may differ.
- **Admin.** The list is sorted by the time an error was last seen, newest first. Each error shows:
  - name and latest message, source and location in code;
  - first and last seen, count, and frequency per day;
  - severity (low, medium, high, critical), editable in the list.
- **Traces.** The latest occurrences of each error are kept with the request or task context and the full stack. The stack shows source lines and local variables, as on Django's debug page, with sensitive values masked.
- **Translations:** English and Russian.

## Requirements

- Python 3.11 or later.
- Django 5.0 or later, tested with Django 6.1.
- Optional: Django REST framework and Celery.

It works with any database that supports Django's `JSONField`, and is tested on PostgreSQL and SQLite.

## Installation

1. Copy the `errors` directory into your project next to your other apps, or into any directory on the Python path.

2. Add the app to `INSTALLED_APPS`. It needs the admin.

   ```python
   INSTALLED_APPS = [
       'django.contrib.admin',
       # ...
       'errors',
   ]
   ```

3. Put the middleware **first** in `MIDDLEWARE`. Then it also sees the 500s that Django makes of exceptions in the other middleware.

   ```python
   MIDDLEWARE = [
       'errors.middleware.ErrorCaptureMiddleware',
       # ...
   ]
   ```

4. Create the tables:

   ```
   python manage.py migrate errors
   ```

5. If you use Celery, restart the workers. The app connects to Celery's `task_failure` signal when Django loads in the worker, so no Celery configuration is needed.

6. Optional: send the `errors` logger to a handler. It logs, with a traceback, any error that could not be recorded, for example while the database is down.

   ```python
   LOGGING = {
       # ...
       'loggers': {
           'errors': {'handlers': ['file'], 'level': 'INFO'},
       },
   }
   ```

Errors appear in the admin under **Server errors**. Users need the view permission on errors to see them, and the change permission to set severity.

## Settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `ERRORS_MAX_TRACES` | `10` | Occurrences kept per error, older ones are deleted. The count keeps the total. A trace with local variables takes tens of kilobytes. |

## Sensitive data

For each occurrence, the app stores:
- the message and traceback;
- the stack, with source lines and local variables;
- the request's method, path, query parameters, status, view, route, site, user id and client IP.

It does not store the request body, cookies, headers or settings.

What is masked:
- **By name:** query parameters, local variables and dictionary keys at any depth whose names contain `API`, `AUTH`, `TOKEN`, `KEY`, `SECRET`, `PASS` or `SIGNATURE`, as in Django's `SafeExceptionReporterFilter`.
- **Decorated functions:** all local variables of functions decorated with `@sensitive_variables`, and of every function they call. Also POST parameters named in `@sensitive_post_parameters`. Django applies these two only when `DEBUG` is `False`.
- **Requests:** request objects are shown as method and path only, because their repr includes the query string.

Name masking does not reach secrets inside other objects' representations, such as a serializer holding the raw input. Decorate views and tasks that handle passwords, one-time codes or payment data with `@sensitive_variables()`:

```python
from django.views.decorators.debug import sensitive_variables

@sensitive_variables()
def login(request):
    ...
```

Local variables may also contain personal data. Grant the view permission on errors only to those who may see it.

## Tests

In a project that has the app installed:

```
python manage.py test errors
```

Without a project, on SQLite, from the directory that contains `errors`:

```
python -m django test errors --settings=errors.tests.settings
```

Tests of the Django REST framework and Celery integration are skipped when those packages are not installed.

## Translations

The source strings are English, and `locale/` holds the English and Russian catalogs. To update them after changing strings, run this in the `errors` directory (it needs GNU gettext):

```
django-admin makemessages -l en -l ru
django-admin compilemessages
```

## Limitations

- Errors are written synchronously by the process that failed. If the database is unavailable, an error is only logged.
- It is a lightweight tracker for a site's own admin. It has no sampling, notifications or retention beyond the per-error trace limit. For high volumes, use a dedicated error tracker.
