# Playwright and local backend verification

These instructions supplement the repository root `AGENTS.md`. Use them for running tests as well as editing this directory.

## Backend safety and fixtures

- Run local API investigation and E2E verification against Django at `http://127.0.0.1:8000`, never production. Set `API_SERVER` for both the frontend server and Playwright; setting it only for tests cannot change an already-running server. Existing environment variables take precedence over `.env`.
- Import `test` and `expect` from `./fixtures`. The auto `blockApiWrites` fixture aborts unmocked non-GET `/api/v0/` browser requests and fails the test. Keep analytics blocking so test purchases are not recorded.
- Mock every write/side-effect endpoint, even with local Django: its production-derived database includes real SMS credentials. In particular, `users/*/check/` sends real SMS. Browser route guards do not cover server-side fetches or APIRequestContext calls, and GET is not a guarantee of no side effects.
- Use the `backend` fixture from `fake-backend.ts` for user flows, extending it with Django's actual response codes/messages when needed. It handles browser requests only; unhandled GETs fall through to Django. Do not try to authenticate server rendering by seeding the browser fake.
- Seed with `addUser`, `signIn`, `addOrder`, `addFavorites`, `addBasket`; use `lastSmsCode(phone)` and `lastEmailLink(email)` instead of real messages. `contract.ts` validates both requests and fake responses against OpenAPI; do not weaken it to make a mismatch pass.
- Product GETs can recalculate and save invalidated stock in Django. Keep them local; for performance comparisons warm up first or request `fields=` that exclude `instock`.

## Running checks

- Run `npm run lint`, `npx next typegen`, then `npx tsc --noEmit` sequentially before relevant browser checks. Do not run lint, tsc or builds concurrently with Playwright: dev compilation contention can cause misleading timeouts.
- Standard local run: `API_SERVER=http://127.0.0.1:8000 npm run test:e2e`. `playwright.config.ts` starts `npm run dev` on HTTP port 4004, or reuses a server already listening there, and uses two local workers. Filter with `--project=chromium`, a filename, or `-g`.
- Configured projects: chromium, firefox, webkit, Mobile Chrome and Mobile Safari. Use the affected projects during iteration and the full matrix for cross-browser UI changes. Install required browser binaries through the project's Playwright tooling; follow global instructions if system packages are missing.
- Next permits one dev server per checkout. If the user's `npm run dev` is already on 4004, leave it running: Playwright reuses it, and an `API_SERVER` set only for Playwright does not change the backend it renders from (it reads `.env`, which names production). Reuse it only after confirming it uses local Django; otherwise ask the user to restart it with the override, stop it, or use an isolated checkout.
- A scratch Playwright config for a server on another port can spread the repository config and set `webServer: undefined`, `use.baseURL` to that server, and absolute `testDir` and `globalSetup` paths. Preserve the other `use` options. A config outside the repo must resolve `@playwright/test` from this checkout's `node_modules`.
- CI builds with `PLAYWRIGHT_TEST=true`, places `.next/static` and `public` under `.next/standalone/`, then runs `PORT=4004 node .next/standalone/server.js` with four test workers and two retries. Locally, `public/` can be large: use a symlink to it when preparing standalone output rather than duplicating it unnecessarily.
- Revalidation requires a production server. Build with `API_SERVER=http://127.0.0.1:8000 PLAYWRIGHT_TEST=true npm run build`, prepare standalone assets, then run `API_SERVER=http://127.0.0.1:8000 CI=1 npx playwright test tests/revalidate.spec.ts --project=chromium` with `REVALIDATION_TOKEN` configured. This checks `x-nextjs-cache`; dev mode skips the cached-page assertions.

## Local Django and schemas

- Check port 8000 for a user-owned server before starting one. If needed, run `.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload` from `../django-shop`, recording its PID. Stop/restart only your own process. With `--noreload`, backend edits require a restart.
- Use the existing `SiteProfile.frontend_key` matching the storefront's `FRONTEND_KEY`; inspect rather than overwrite it. `Origin` no longer selects the API site. Do not infer the active cookie names from old sessionid examples; check Django settings.
- `global-setup.ts` downloads `${API_SERVER}/api/v0/schema/?format=json` with `API_TOKEN` and caches it in `tests/.cache/openapi.json` for an hour. Clear that cache when changing backend code or switching backend hosts; it is not keyed by host. A failed refresh may reuse an older cached schema, so check warnings.
- To test an unreleased schema, generate it from django-shop with `.venv/bin/python manage.py spectacular --settings=tests.settings --skip-checks --format openapi-json --file /tmp/cartzilla-openapi.json`, then set `API_SCHEMA=/tmp/cartzilla-openapi.json`. Investigate current schema errors rather than assuming historical errors still apply.
- If backend tests or migrations are needed, follow django-shop's own instructions and virtualenv. Do not alter the local database role or mutate the `sworld` database for verification. Use a disposable PostgreSQL cluster and, for real-data checks, a copy of the database.
- The recorded cluster setup uses PostgreSQL 17 binaries in `/usr/lib/postgresql/17/bin`, `initdb -A trust -U andrey --locale=C.UTF-8 -E UTF8`, and `pg_ctl` with `-p 55432 -c unix_socket_directories='' -c listen_addresses=127.0.0.1 -c fsync=off`. Verify available binaries/port first. TCP avoids Unix socket path-length limits. Scope trust/fsync settings to this disposable loopback cluster.
- Run backend tests with `DATABASE_URL=postgres://andrey@127.0.0.1:55432/postgres .venv/bin/python manage.py test tests --settings=tests.settings`; Django creates/destroys its test database. Stop your cluster and remove its sensitive dumps/data after use. A copied database still has customer data and SMS credentials.

## Reliable assertions and diagnosis

- Select controls by role, label and text; keep accessible labels for icon-only buttons. Use the existing hydration helpers and retryable assertions before interacting with SSR-rendered controls. Wait for the actual state/response a flow needs, not merely page load.
- Dev StrictMode can issue effects twice; assert meaningful requests/results rather than exact effect counts. First route compilation can be slow. Rerun dev timing failures with `--last-failed --workers=1` before classifying them, and investigate persistent failures.
- Avoid `networkidle` as a readiness signal; Next prefetching can remain active. Use visible state or explicit response assertions. Old notes saying `/pages/*` necessarily 404s under `PLAYWRIGHT_TEST=true` are obsolete; content pages now render on demand.
- Whole-pack basket tests must wait for the real `sites/current` answer and quantity input `step`; the fake basket can arrive first. Preserve coverage for quantities entered before wholesale settings arrive.
- Use traces to identify stalled images/requests. Diginetica search can time out independently of Django. Missing local media and Next's private-IP image restrictions are distinct from application failures; `next.config.ts` already derives a remote pattern from `API_SERVER`.
- Repeated backend 500s with PostgreSQL connection-slot errors can come from threaded runserver connections retained by `CONN_MAX_AGE`; restart your own server rather than treating this as a React bug. Do not dismiss unexplained timeouts as environmental without checking evidence.
- For cross-site security tests against 127.0.0.1, serve the attacking page from `http://localhost:<port>`: Chromium Local Network Access can block a public-origin replay before it reaches the proxy.
- A Base UI menu that opens then closes on Mobile Safari may be moving between pointerdown/up. Check layout shifts first; WebKit lacks the layout-shift PerformanceObserver, so compare element bounds across animation frames.
