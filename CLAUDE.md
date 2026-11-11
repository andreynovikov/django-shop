# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 6.1 backend for the "Швейный Мир" (sewing-world.ru) family of e-commerce sites. Code, comments, verbose names and UI strings are mostly in Russian. This repository is the **backend only**: storefronts are separate Next.js apps that talk to the REST API here and get cache-revalidated via `revalidate_nextjs` in `shop/tasks/workflow.py`.

The same codebase is deployed many times, once per site (sewing-world, janome, singer, wholesale, etc.), each from its own long-lived git branch (see `git branch -a`) with its own virtualenv and `.env`. `main` is the shared base; changes are usually merged into site branches afterward.

## Commands

Project tests are in `tests/`, and the `errors` app has its own in `errors/tests/`. `.github/workflows/tests.yml` runs flake8 and both suites on every push, against a PostgreSQL 16 service container (production's major version). The other workflow builds a Docker image from the `cartzilla` branch.

Dependencies are managed with uv. `pyproject.toml` lists only the packages the code uses directly, plus flake8 in the `dev` group, and `uv.lock` pins everything. Add packages with `uv add` and upgrade with `uv lock --upgrade-package <name>`. `override-dependencies` lifts the `Django<6.1` that django-celery-beat and django-prometheus declare. Servers keep their virtualenv in `env/`, see DEPLOYMENT.rst.

```bash
uv sync && source .venv/bin/activate    # or prefix the commands below with `uv run`
flake8                                  # lint; E501 (line length) is ignored, see .flake8
python manage.py check
python manage.py test tests errors --settings=tests.settings   # needs a Postgres role with CREATEDB, see tests/settings.py
python manage.py runserver
python manage.py makemigrations <app>
celery -A sewingworld worker -Q default,priority,integrations,import,revalidation
celery -A sewingworld beat              # schedules are stored in the DB (django_celery_beat)
python manage.py rerun_task <task_id>   # re-run a stored Celery task result
python manage.py cleanup_legacy_phones  # repair or remove accounts whose phone is not +7; reports only, --apply changes
python manage.py backup_db --dry-run    # hourly pg_dump into restic; --kind full|hot|config forces a kind
```

Running anything requires:
- A `.env` in the repo root (read by `django-environ`). Required keys include `SECRET_KEY`, `DATABASE_URL` (PostgreSQL), `CACHE_URL` (memcached), `ALLOWED_HOSTS`, `ALLOWED_ORIGINS`, `ROOT_URLCONF`, `CELERY_BROKER_URL` (Redis), `ADMINS` (`name:email,...`), `LOGIN_URL`/`LOGIN_REDIRECT_URL`/`LOGOUT_URL`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, `CSRF_COOKIE_SAMESITE`, `SESSION_COOKIE_SAMESITE`.
- `sewingworld/settings/integrations.py`. It is gitignored because it holds marketplace and payment credentials, but `settings/__init__.py` imports it unconditionally.
- A `logs/` directory, which the file log handlers write to.

## Architecture

### Settings and the two deployment modes
`DJANGO_SETTINGS_MODULE=sewingworld.settings`. That is a package: `__init__.py` reads env vars and then star-imports the topic modules (`apps`, `celery`, `constance`, `middleware`, `shop`, `integrations`, `logging`, ...). Add new settings to the matching topic module.

The `ADMIN=True` env var switches the process into **admin-site mode**. It also loads `.env.admin` on top of `.env`, and `sewingworld/urls.py` then serves only the 2FA-protected Django admin (`two_factor`, `massadmin`, `loginas`). Otherwise the process serves the public REST API at `/api/v0/` plus a few payment and document endpoints. The admin and the API run as separate uWSGI apps from the same code.

### Multi-site
Uses `django.contrib.sites` plus `sewingworld.models.SiteProfile` (root category, wholesale flag, order prefix, YooKassa credentials, Next.js revalidation token, domain aliases). For API requests, `SiteDetectionMiddleware` sets `request.site` from the `Origin`/`Referer` header, matching against `Site.domain` or `SiteProfile.aliases`, so API code should use `request.site` and not `SITE_ID`. Sessions can travel in an `X-Session` header (`SessionCookieMiddleware`) for clients that block cross-site cookies.

### Apps
- `sewingworld/`: project package and also an app. It holds the REST API (views in `api/`, serializers in `serializers/`, both bundled as catalog, shopping, orders, users, content and integrations, with shared pieces in `common.py`; a DRF router in `urls.py`), the product list's filters and facets (`filters.py`), the custom admin site (`admin.py`, `SWAdminSite`), SMS gateways (`sms.py`, `smsru.py`, `sms_uslugi.py`; the provider is chosen through constance), and middleware.
- `shop/`: core domain. Models are split into `shop/models/*.py`, a module per model together with the models that only serve it (`Product` and `ProductImage`), and re-exported through `__all__` in `shop/models/__init__.py`, so a new model module has to be added there. Admin is split the same way in `shop/admin/`. The order admin keeps its business logic in `order_supply.py` (stock for suppliers), `order_shipping.py` (boxes, delivery, labels, acts, 1C export) and `order_editing.py`, and its list filters in `order_filters.py`. `AUTH_USER_MODEL = 'shop.ShopUser'`.
- `shop/tasks/`: Celery tasks in bundles: `user_interaction` (SMS and mail to customers), `admin` (notices to staff), `workflow` (order updates, product revalidation, basket expiry), `stocks` (stock and price import from 1C through Yandex Disk) and `integrations` (bonuses from 1C, currency rates, ModulPOS, Yandex Metrika). Each task is named `shop.tasks.<function>` explicitly, the name it had in the former `shop/tasks.py`, because beat schedules in the DB, stored results and queued tasks refer to it. Name new tasks the same way.
- Users: the API accepts +7 phones only (`PhoneValidator`). Registration and moving to another phone need a code sent to that phone (`PhoneCode`); accounts made silently at checkout keep `phone_verified=False` until an SMS login. Customer mail goes only to a confirmed address (`email_verified`, set by the link in `shop/email_confirmation.py` or by staff), and order mail waits for it (`confirmed_email` and `postpone_mail` in `shop/tasks/user_interaction.py`).
- Marketplace and payment integrations, each with `tasks.py` and usually `signals.py`: `beru` (Yandex Market), `ozon`, `wb` (Wildberries), `sber` (SberMegaMarket), `yandex_kassa` (YooKassa), `yandex_delivery`, `rarus` (bonus program). `unisender` and `mptt_urls` are plain helper modules, not installed apps.
- `errors/`: server errors grouped for the admin only, written as an independent app like `reviews`. It must not import project code, its strings are English with `en`/`ru` catalogs in `errors/locale/`, and `errors/README.md` documents it. `ErrorCaptureMiddleware` (first in `MIDDLEWARE`) records every 5xx response, and a `task_failure` receiver records Celery tasks that fail for good. Repeats of an exception from the same view or task and the same project function count into one `Error`, which keeps its latest traces with masked locals. Mark functions that hold secrets with `@sensitive_variables()`, which also masks the frames they call.
- `blog/`, `forum/`: content apps. `forum` models are `managed = False` and map onto legacy tables, so they have no migrations.

### Product filters and facets
`ProductFilterSet` in `sewingworld/filters.py` declares every parameter of the product list; any other is ignored, so a new one has to be declared there. The storefronts send those in `productSearchParams` (`src/lib/search-params.ts`), ranges as `price=a-b`. `Category.filters` names the filters a category page shows. `CategorySerializer` describes them, and the product list of that category brings their choices and ranges as `filters`, counted over the products that the other parameters find. A full-text search brings `manufacturer` and `price` the same way. The storefronts pick a control by `class`, or by `widget` for the sliders (`ShopRangeWidget`, `ShopSliderWidget`). These names come from Django forms that are no longer used, but keep them.

### Integrations pattern
`shop.models.Integration` (keyed by `utm_source`) describes a sales channel. Its per-channel config lives in the `settings` JSONField (for example `ym_campaign` or `warehouse_id`), and `ProductIntegration` stores per-channel price and a `notify_stock` flag. Integration apps hook `post_save` on `Product`/`Order` and queue Celery tasks to push stock and order status. Orders from channels with `uses_api=True` skip the normal customer-notification flow in `shop/signals.py`.

### Side effects through signals and Celery
Order status changes are watched with `django-model-utils` `FieldTracker` (`order.tracker.has_changed('status')`), and the `post_save` receivers in `shop/signals.py` and each integration's `signals.py` dispatch SMS, email, manager notifications, POS sync and storefront revalidation as Celery tasks. Saving a model can therefore queue background work. Setting `product.num = -1` is the convention for "stock needs to be re-reported". Reading `product.instock` then counts it and saves only `num`. `import1c` resets it for every product it imports and queues `count_stocks`, which counts them in the worker so that API requests don't have to.

Tasks are routed to named queues (`priority`, `integrations`, `import`, `revalidation`, `default`) and most use `autoretry_for`/`retry_backoff`. Results go to the DB (`django_celery_results`). The `PRIORITY_*` constants in `sewingworld/tasks.py` are currently `None`, so priorities are effectively disabled. Runtime-editable settings such as the default seller or SMS provider live in `django-constance` (`sewingworld/settings/constance.py`).

### Query counts
API time goes mostly to Python, and grows with the number of queries per request. Product serializers have a `prefetch()` classmethod that adds the `only()` columns and the prefetches they need (a product row has about 150 columns), so pass a queryset through it before serializing products. `Product.site_price_record()` reads prefetched `site_prices`. `DISTINCT` over product rows is costly, so filters through many-to-many relations (`in_category`, `kind`) use a subquery instead of a join, and `ProductViewSet` orders ties by `pk`. Tests check that query counts don't grow with the objects shown (`count_queries` in `tests/clients.py`).

### Backups
`sewingworld/management/commands/backup_db.py` runs hourly from a systemd timer and streams `pg_dump` into a restic repository (`RESTIC_*` in `.env`) on an append-only rest-server. It makes a full dump daily and after migrations, and otherwise a hot dump of the `DB_BACKUP['HOT_MODELS']` rows only (`sewingworld/settings/backup.py`). Full runs also save `.env` and `integrations.py`. The backup host runs `deploy/backup/maintain.sh` (retention, alarms, weekly restore test), and `deploy/backup/restore.sh` lays the latest hot dump over its full dump. A new model whose rows change often belongs in `HOT_MODELS`. A table of logs belongs in `EXCLUDE_DATA_APPS`. DEPLOYMENT.rst has the setup and the restore runbook.

### Infrastructure
PostgreSQL (the DB backend is wrapped by `django_prometheus`, and the code relies on Postgres features: `ArrayField`, JSON lookups, FTS), memcached, Redis as the Celery broker, and uWSGI behind nginx. `DEPLOYMENT.rst` describes the server setup (Debian, systemd units for uWSGI and Celery, master/slave failover, the per-site `/www/<domain>` layout). The 1C stock import reads from `SHOP_IMPORT_DIRECTORY` (`/www/www.sewing-world.ru/import`).
