# django-shop

## Scope and architecture

- Django backend for the Швейный Мир family of shops: Python 3.13, Django 6.1, DRF, PostgreSQL, Celery/Redis and memcached. Dependencies and exact versions live in `pyproject.toml` and `uv.lock`. Verbose names and UI text are in Russian; keep them so. Code comments are in English.
- The backend lives on `main` and is deployed manually. Other branches (`sworld`, `family`, `janome`, `singer`, `dortak`) contain Next.js storefronts. Never merge backend changes into those branches. Consult `deploy/README.md` and provide the manual deployment steps relevant to a backend change (migrate, collectstatic, uWSGI/Celery reload, and the Ansible tag when nginx, units or storefront deployment change).
- This file is the project's only instruction file. `CLAUDE.md` just imports it for Claude Code, so put guidance here, never there. Keep reusable preferences out of it (`~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`). Current code and CI win over stale details; historical rollout status and private operational findings don't belong here.
- `sewingworld/` is both the project package and an app. REST views and serializers are grouped by domain (catalog, shopping, orders, users, content, integrations, shared pieces in `common.py`) in `sewingworld/api/` and `sewingworld/serializers/`; routing is a DRF router in `sewingworld/urls.py`, product filters and facets in `sewingworld/filters.py`. It also holds the custom admin site (`admin.py`, `SWAdminSite`), the SMS gateways (`sms.py`, `smsru.py`, `sms_uslugi.py`; the provider is chosen in constance) and the middleware.
- `shop/` holds the domain. Models/admins are split into `shop/models/` and `shop/admin/`; export new models through `shop/models/__init__.py` and its `__all__`. Keep order-admin logic in `order_supply.py`, `order_shipping.py` and `order_editing.py`, and list filters in `order_filters.py`. The user model is `shop.ShopUser`.
- `DJANGO_SETTINGS_MODULE=sewingworld.settings` is a package: `__init__.py` reads the environment and star-imports the topic modules (`apps`, `celery`, `constance`, `middleware`, `shop`, `integrations`, `logging`, …); add settings to the matching topic module. `ADMIN=True` loads `.env.admin` over `.env` and selects the 2FA admin (`two_factor`, `massadmin`, `loginas`); otherwise serve the public API at `/api/v0/` and payment/document endpoints. API and admin are separate uWSGI apps sharing the code.
- `blog` and `forum` are content apps. Forum models use legacy tables with `managed = False`; do not create migrations to manage those tables.
- Integrations include `beru` (Yandex Market), `ozon`, `wb`, `sber`, `yandex_kassa`, `yandex_delivery` and `rarus`. `unisender` and `mptt_urls` are helpers, not installed apps. The bonus program and its 1C bonus import are retired despite remaining code/fields; the 1C stock/price import is still active.

## Dependencies and setup

- Use uv and `.venv`: `uv sync --locked`, then prefix Python commands with `uv run --no-sync`. Add direct dependencies with `uv add`; update a package with `uv lock --upgrade-package <name>`. Keep `uv.lock` in step.
- Preserve the Django override required by django-celery-beat and django-prometheus and the `django-more-admin-filters` fork on `simple-list-filter` (it provides `SimpleDropdownFilter`).
- Normal runtime needs a root `.env` (read by django-environ), the gitignored `sewingworld/settings/integrations.py` (marketplace and payment credentials, imported unconditionally) and a `logs/` directory for the file log handlers. Required `.env` keys include `SECRET_KEY`, `DATABASE_URL` (PostgreSQL), `CACHE_URL` (memcached), `ALLOWED_HOSTS`, `ALLOWED_ORIGINS`, `ROOT_URLCONF`, `CELERY_BROKER_URL` (Redis), `ADMINS` (`name:email,...`), `LOGIN_URL`/`LOGIN_REDIRECT_URL`/`LOGOUT_URL`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, `CSRF_COOKIE_SAMESITE` and `SESSION_COOKIE_SAMESITE`; the settings modules and the deployment guide have the rest. Do not copy credentials into instructions or tracked files.
- `--settings=tests.settings` supplies missing env defaults, an integrations-module stub and logging configuration, so tests do not require those local files. They still need PostgreSQL and a role with `CREATEDB`; set `DATABASE_URL` explicitly to the intended test server. Do not substitute SQLite: the backend relies on PostgreSQL arrays, JSON lookups and full-text search.
- Local untracked clones and the `more_admin_filters` symlink can shadow installed packages. For CI parity, export tracked files plus intended new files to a scratch checkout, excluding clones, and use locked dependencies.

## Verification

```bash
uv sync --locked
uv run --no-sync python manage.py check --settings=tests.settings
uv run --no-sync python manage.py test tests errors filemanager --settings=tests.settings
# Avoid traversing local untracked clones:
git ls-files -z '*.py' | xargs -0 uv run --no-sync flake8
```

Other commands (prefix with `uv run --no-sync`):

```bash
python manage.py runserver
python manage.py makemigrations <app>
celery -A sewingworld worker -Q default,priority,integrations,import,revalidation
celery -A sewingworld beat              # schedules are stored in the DB (django_celery_beat)
python manage.py rerun_task <task_id>   # re-run a stored Celery task result
python manage.py cleanup_legacy_phones  # repair or remove accounts whose phone is not +7; reports only, --apply changes
python manage.py backup_db --dry-run    # hourly pg_dump into restic; --kind full|hot|config forces a kind
python manage.py postman_spec /tmp/spec.json  # OpenAPI spec of the Postman collection, see postman/README.md
```

- Add new Python files to the lint invocation. `.flake8` ignores E501; follow existing formatting and PEP 8 otherwise. CI runs `uv run --locked --only-dev flake8` in a clean checkout.
- Use unittest/Django test cases in `tests/` and explicit test labels. Only `errors` and `filemanager` dependency tests belong in the backend suite; other packages may require their own settings and `auth.User`.
- `.github/workflows/tests.yml` uses PostgreSQL 16. Backup/restore checks need matching PostgreSQL client tools, `jq` and restic >= 0.17; append-only server checks use `restic-rest-server`. A skipped prerequisite check is not verification.
- If the local role cannot create databases, use an available private PostgreSQL cluster on TCP `127.0.0.1` with a short socket path or disabled Unix sockets. Report any major-version difference from CI. Review generated migrations for unrelated model drift before keeping them.
- For API/storefront verification, use local Django and explicitly set frontend `API_SERVER=http://127.0.0.1:8000`; its `.env` may point at production. Reuse the user's running server. Restart your own `--noreload` server after backend changes and stop it only by its PID.
- Storefront Playwright tests live in `~/Workspace/cartzilla`. Tests that write must use its `backend` fixture; keep `blockApiWrites` enabled. The local database also contains real integration/SMS configuration, so local writes are not automatically harmless.
- Generate a schema with `uv run --no-sync python manage.py spectacular --settings=tests.settings --format openapi-json --file /tmp/django-shop-schema.json`, then set `API_SCHEMA` to that path for frontend contract tests. Refresh frontend `tests/.cache/openapi.json` after backend changes.
- Diagnose backend latency, stale servers/schema and connection exhaustion before attributing Playwright timeouts to frontend regressions. Threaded runserver plus persistent connections can exhaust PostgreSQL slots; restart only a server you own when needed.
- Run relevant tests, check lint/formatting, and report changes, verification and unresolved issues. Check normal runtime settings as well when changing deployment/environment configuration.

## Sites and API contracts

- `SiteProfile` extends `django.contrib.sites` with root category, wholesale mode, order prefix, aliases, payment credentials and frontend/revalidation keys. API code must use `request.site`.
- For `/api/v0/`, `FrontendKeyMiddleware` selects the site by `X-Frontend-Key` and accepts `X-Real-IP` from a valid storefront. Without a valid key, it uses the default site, ignores session cookies and permits writes only with token authentication. Outside this API path, `SiteDetectionMiddleware` selects the site from `Origin`/`Referer`, matching `Site.domain` or `SiteProfile.aliases`; it is not a replacement for the key. Preserve browser `Origin` forwarding for CSRF checks.
- `SecurityMiddleware` sends nosniff, Referrer-Policy and COOP on every response, errors included. nginx adds HSTS and redirects to HTTPS, so `SECURE_SSL_REDIRECT` stays off.
- Use the existing local `SiteProfile.frontend_key` for site-specific tests. Preserve and restore any key temporarily changed. Default-site reads can look correct even when a frontend key is rejected.
- `settings.SITE_ID` (1, www.sewing-world.ru) identifies the main site whose in-progress orders reserve stock (see `Product.get_stocks()`); this rule is distinct from request-site selection.
- Declare product-list parameters in `ProductFilterSet` and OpenAPI. Unknown filters are ignored by the backend but rejected by storefront contract tests. Coordinate changes with storefront `src/lib/search-params.ts` (`productSearchParams`).
- Preserve range syntax (`price=a-b`, `cost=a-b`), `variations=` meaning no variations, and `ta=1` returning title strings. `text` with `ta` must preserve relevance order; empty `ordering=` must not discard it.
- `price` is list price; `cost` includes site discounts. Keep `Product.site_cost()` and SQL equivalent `Product.with_site_cost()` consistent for filtering, facets and ordering. Retain `price` compatibility and price bounds in sitemap/XML feeds.
- `Category.filters` selects visible filters. Metadata includes `id`, `label`, `unit`, `choices`, `attrs.step/min_value/max_value`, `class` and `widget`. Preserve API strings `NullBooleanField`, `ChoiceField`, `MultipleChoiceField`, `ShopRangeWidget` and `ShopSliderWidget` even though their original Django widgets are gone. Facets reflect other active filters.
- `NonNullModelSerializer` omits null, empty-string and empty-list fields; account for this in types/consumers. Use `NumberReadOnlyField`/`IntegerReadOnlyField` for numeric properties and return annotations on serializer methods. Explicit schema response mappings must retain success responses alongside errors.

## Accounts and communication

- API phone validation accepts `+7` only; do not indiscriminately apply it to marketplace/system records. Registration and phone changes require an SMS code (`PhoneCode`). Silent checkout/preorder/warranty accounts remain unverified until SMS login; first verification resets email verification.
- Passwords require at least eight characters without complexity rules. There is no password lockout. Reveal an occupied email only after a correct SMS code; phone/username availability remains part of initial validation.
- Customer mail requires `email_verified`, set by the link from `shop/email_confirmation.py`; staff confirmation counts. Order mail waits for confirmation and retries for up to seven days (`confirmed_email`/`postpone_mail` in `shop/tasks/user_interaction.py`).
- Keep basket restore/clear and logout as POST operations. Preserve CSRF/session protections and the cookie compatibility period described below.

## Signals, tasks and stock

- Model saves can enqueue SMS, mail, marketplace updates, POS sync and revalidation. Order receivers use `FieldTracker` for status changes. Queue work requiring committed state with `transaction.on_commit`.
- Keep `before_task_publish` PENDING result records in `sewingworld/signals.py`; the user relies on them for monitoring. Do not remove them as a lock-contention workaround.
- Celery bundles in `shop/tasks/` are `user_interaction` (SMS and mail to customers), `admin` (notices to staff), `workflow` (order updates, storefront revalidation, basket expiry), `stocks` (stock and price import from 1C through Yandex Disk) and `integrations` (retired 1C bonuses, currency rates, ModulPOS, Yandex Metrika). Preserve explicit task names `shop.tasks.<function>`: persisted schedules, queued tasks and stored results depend on them.
- Routes use `default`, `priority`, `integrations`, `import` and `revalidation`. Preserve appropriate retries/backoff. Beat schedules and results live in the database; runtime business settings use django-constance. `PRIORITY_*` constants in `sewingworld/tasks.py` are currently `None`.
- `Integration` is keyed by `(target_site, utm_source)`. The target storefront scopes the API and storefront checkout attribution. `source_site` identifies the sales channel and supplies feed pricing and marketplace order sites. Channel configuration lives in JSON `settings`; `ProductIntegration` carries prices and `notify_stock`. Orders with `uses_api=True` bypass normal customer notifications.
- `product.num = -1` means recount stock. Reading `instock` may save `num`; retain `Product.save_stock()` so post-save receivers run. Bulk import queues `count_stocks`, which uses `Product.get_stocks()` in batches.
- Count marketplace/feed stock in bulk with `Product.get_stocks()`. Sets use each part's stock at the integration's suppliers, including express rules. Clamp computed stock at zero; negative stock must not become a perpetual recount marker.

## Revalidation and performance

- Storefront pages are static and re-rendered by tag: storefronts tag their page requests (`category:<id>`, `product:<code>`, `catalog`, …) and receive changed tags at `/api/revalidate`; `revalidate(tags, sites)` sends them. Keep `shop/revalidation.py` tags aligned with storefront `lib/queries/cache-tags.ts`. A new model shown on a static page needs backend change receivers and tags on frontend requests.
- Revalidation batches per transaction and sends on commit, once per site through `revalidate_nextjs`. Outside transactions it sends immediately; bulk updates must collect IDs and call `revalidate_products()` once.
- `revalidate_products()` includes affected lists, actions and related accessory/set pages; `revalidate_product_pages()` is narrower; `revalidate_stock()` compares stock before/after commit. Edits/prices expire immediately; stock uses background stale-while-revalidate. Update `shop/signals.py`'s `REMEMBERED` when old slugs, URLs or relationships matter.
- Apply product serializers' `prefetch()` before serialization to select necessary columns/relations from wide product rows. Reuse prefetched `site_prices`, batch stock, avoid wide-row `DISTINCT` through many-to-many joins, and preserve `pk` as an ordering tie-breaker.
- Use `count_queries` in `tests/clients.py` to ensure query counts do not grow with result size. Past profiling found no speedup from psycopg 3, pooling or additional general indexes; investigate query counts/Python work first unless new evidence warrants those changes. A driver migration must also address psycopg2 `cursor.copy_from` in stock import.
- For local benchmarks, measure cold/warm stock states, roll back incidental writes, set the proper frontend key and allowed host, and clear `connection.queries_log` before capture to avoid its 9,000-query cap.

## Admin HTML and independent packages

- Clean editor HTML in backend admin forms, not storefront repair code or model `save()`. Products, adverts and stores use `shop.tidy.tidy_html5` with HTML5 and empty-element preservation; news retains strict cleanup. Comment-only content may become empty.
- Change/test `errors` (`django-server-errors`), `filemanager` (`django-admin-filemanager`), `reviews` (`django-rated-reviews`) and other independently maintained packages in their own repositories, then consume releases here. Do not patch installed packages or rely on local clones in the final change.
- `ErrorCaptureMiddleware` (first in `MIDDLEWARE`) records 5xx responses; final Celery failures are also captured. Repeats of an exception from the same view or task and project function count into one `Error`, which keeps its latest traces with masked locals. Mark functions handling secrets with `@sensitive_variables()` to mask captured frames and their callees.
- `filemanager` is the admin's browser for files that HTML text links to (`MEDIA_ROOT`, in place of FTP): replacing a file keeps its URL, and "where used" searches the admin models' `TextField`s. Add new file-field `upload_to` folders to `FILEMANAGER_PROTECTED` in `sewingworld/settings/admin.py`. Use `HTMLTextarea` only for fields rendered as HTML by storefronts, updating `tests/test_html_fields.py` and the admin form together.
- Independent packages release from annotated `vX.Y.Z` tags through publishing workflows. Obtain explicit push/release authorization unless already given. After release, refresh stale index metadata with `uv add --refresh-package <pkg> '<pkg>>=<version>'`, or upgrade the lock entry as appropriate.
- Translation tests expecting English must activate `en` because test settings default to Russian. Preserve catalog source locations; independent apps need English catalogs as well as Russian ones.

## Operations and private references

- Infrastructure: PostgreSQL (a DBaaS on another host; the DB backend is wrapped by `django_prometheus`), memcached, Redis as the Celery broker, and uWSGI behind nginx on Debian, with one `/www/<domain>` directory per site. The 1C stock import reads from `SHOP_IMPORT_DIRECTORY` (`/www/www.sewing-world.ru/import`).
- Read `deploy/README.md` and `deploy/ansible/README.md` before infrastructure changes. The playbook `deploy/ansible/site.yml` (roles `server`, `backup_host`) manages packages, users, sshd/OTP, nftables, uWSGI/Celery units (apps, processes and threads in `roles/server/defaults/main.yml`), certbot's reload hook, backups, log rotation, the daily `docker-prune.timer` and storefront deployment. TLS files, `/etc/nginx/htpasswd`, OTP secrets, the backend checkout with `.env`, the storefronts' `.env.storefront` (their configuration, mounted into the containers; see "Storefront configuration" in `deploy/README.md`) and storefront feed templates stay manual.
- The complete nginx configuration (`nginx.conf`, all sites, `sw_proxy_params`, snippets) lives in `roles/server/files/nginx/`. Change it there, not on the server; the `nginx` tag installs it, enables `server_nginx_sites_enabled` and runs `nginx -t` before reload. Site logs go to `/var/log/nginx`, never into `/www`. Storefront proxies turn 502–504 into a 503 with the storefront's `.docker/public/unavailable.html`.
- The frontend workflow on `main` is an intentional failing stub exposing GitHub's manual deployment button; real workflows live on storefront branches. Deploys log in as `deploy`, whose key runs only the forced command `deploy-frontend <name> <tag>` (`roles/server/templates/deploy-frontend.j2`). It pulls `ghcr.io/andreynovikov/<branch>:<tag>` and starts it with the shared Compose file (`roles/server/files/docker-compose.yaml`, installed as `/etc/sworld/storefront-compose.yaml`) in the site directory, as the `sworld` UID/GID. Storefronts, directories and ports are in `server_frontend_sites`; `stage` runs the `sworld` branch at `/www/cartzilla.sigalev.ru`. Apply the `deployment` tag after changing them.
- Preserve per-connection `lock_timeout=5s` and its propagation to `pg_dump` through `PGOPTIONS`. For deployment lock failures, check `SHOW lock_timeout` through Django: a pooler may discard startup options. Use a `connection_created` setting only if that behavior is confirmed.
- Backups (`backup_db`, hourly from a systemd timer, `RESTIC_*` in `.env`) stream `pg_dump` into append-only restic storage: daily/post-migration full dumps, otherwise hot data (`sewingworld/settings/backup.py`). The backup host runs `deploy/backup/maintain.sh` (retention, alarms, weekly restore test); `deploy/backup/restore.sh` lays the latest hot dump over its full dump. Put frequently changing models in `DB_BACKUP['HOT_MODELS']`, log tables in `EXCLUDE_DATA_APPS`. Full backups also preserve environment/integration configuration. Restore/retention scripts live in `deploy/backup/`.
- `postman/README.md` covers schema generation, import and CLI usage for the Sewing World API workspace. Keep `postman/prerequest.js`, `postman/test.js` and `tests/test_postman_spec.py` synchronized. Retain `allowSideEffects`; CLI runs lack credentials stored only as app current values. Look up current workspace/collection/environment IDs rather than assuming historical IDs still apply.
- This repository is public. Never commit `SERVER.md`, `PROBLEMS.md`, `server_inspection.txt`, credentials, or quotations of their open findings. Consult those gitignored records for infrastructure details and known issues; recheck code before acting. The nginx configuration is published in the role since the recorded weaknesses were fixed; check that an nginx change does not reintroduce one. Keep `inventory.yml` gitignored, TLS keys and `htpasswd` out of git, and hashes/tokens in ansible-vault.

## Compatibility work requiring coordination

- Keep `CookieRenameMiddleware`, the legacy `sessionid` fallback and associated tests until at least **2026-12-07**. Coordinate cleanup with all five storefronts' legacy `csrftoken` support after verifying the transition completed; the date alone does not confirm deployment state.
- `SEARCH_FACETS` still includes `price` and `cost`. Remove the old search facet only once consumers use `cost`; retain the `price` API contract. The user chose to update existing category filter/order data manually after frontend deployment instead of using a data migration. Do not assume that update happened.
