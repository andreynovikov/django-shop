# Cartzilla / sewing-world.ru

## Scope and sources

- This is the Russian-language sewing-world.ru storefront: package `sworld`, branch `sworld`. It has no database; data comes from the separate `../django-shop` backend at `${API_SERVER}/api/v0/`.
- Keep reusable development preferences in `~/.codex/AGENTS.md`; this file contains project-specific instructions. Read [tests/AGENTS.md](tests/AGENTS.md) before running or changing tests.
- Guidance was consolidated from this repository's `CLAUDE.md` and all 23 files in `~/.claude/projects/-home-andrey-Workspace-cartzilla/memory/`, checked against the checkout on 2026-11-23. Original Claude files are preserved. Prefer current code/configuration over historical rollout status.

## Commands and configuration

- Use npm and `package-lock.json`; install project dependencies with `npm ci`.
- `npm run dev`: HTTPS at `https://127.0.0.1:3004`. Certificates are gitignored. On a fresh clone, create `certificates/` and run `mkcert -install -key-file certificates/localhost-key.pem -cert-file certificates/localhost.pem localhost 127.0.0.1 ::1`. Explicit certificate paths avoid Next's IP-host certificate regeneration.
- `npm run test`: starts the HTTP development server at `http://127.0.0.1:4004`; it does **not** run tests.
- `npm run test:e2e`: Playwright. Local verification must use local Django; see the test instructions.
- `npm run build`: standalone production output. `npm start`: production server on port 4004.
- For code changes, run `npm run lint`, then `npx next typegen`, then `npx tsc --noEmit`; typegen must precede tsc. Run relevant Playwright tests separately from lint, type checks and builds. ESLint covers `src/`; there is no separate formatter script.
- Server configuration: `API_SERVER` (host only), `API_TOKEN`, `FRONTEND_KEY`, `REVALIDATION_TOKEN`. Browser configuration includes `NEXT_PUBLIC_YMAPS_API_KEY` and the site's `NEXT_PUBLIC_*_VERIFICATION` values. Keep tokens and the frontend key server-only. `ORIGIN` is obsolete.
- For local builds and API investigation, override `API_SERVER=http://127.0.0.1:8000` in the process environment rather than using production. Keep the existing local site's frontend key; do not overwrite it as setup.

## Application architecture

- Stack: Next.js App Router, React, TypeScript, TanStack Query, nuqs, Tailwind CSS v4, Base UI and Tabler icons. Consult installed Next.js documentation before code changes (managed instructions below).
- Routes live in `src/app/`. `(auth)`, `(pages)` and `(shop)` are organizational route groups. Account pages are under `user/`; other entry points include `blog/`, `actions/`, `pages/[...uri]`, `oldforum/`, `sitemap.ts`, API routes and XML feeds.
- Root `layout.tsx` loads the catalog and renders the shared shell. `providers.tsx` supplies Query, nuqs, site, navigation, session, toast, topbar and toolbar contexts.
- Use the hook-free `pageContentWrapper()` in `src/components/layout/page-content-wrapper.tsx` for server-rendered headers, or its `PageHeader` and `PageTitle` parts.
- Account pages share `user/layout.tsx` and its persistent sidebar. A new page also needs a corresponding `user/@header/.../page.tsx` for title, breadcrumbs and metadata. Account routes are noindex.
- Session, basket, favorites, comparisons and orders load in the browser so their pages can remain static. Do not move personalized state into shared server-rendered output.
- Use `next/navigation` directly. nuqs and `useSearchParams()` in static routes need a small Suspense boundary with a query-independent fallback. Put headers that must remain visible in the segment layout outside `loading.tsx`. Read `window.location` in event handlers when no render-time query subscription is needed.

## Data and API contracts

- Resource modules in `src/lib/queries/` export query-key factories and plain `load*`/`retrieve*` functions through `@/lib/queries`. Use `apiFetch`; shared data types are in `src/lib/types.ts` and shared state/hooks in `src/lib/`.
- Server-side reads go directly to Django. Browser requests use `/api/v0/...`, handled by `src/app/api/v0/[...path]/route.ts`; requests with bodies also use that relative proxy path. The proxy exports GET, POST and PUT.
- `FRONTEND_KEY` becomes `X-Frontend-Key` on server fetches and proxy requests. Django derives the site from it and accepts nginx's `X-Real-IP`. Without a valid key, sessions disappear, writes require a token, and reads fall back to the default site. Sewing-world reads can therefore look correct even with a bad key.
- Preserve the proxy's request-header allowlist, browser Origin forwarding, cookie/Set-Cookie handling, path validation, manual redirects and mutation gate (`X-Requested-With` plus absent or same-origin `Sec-Fetch-Site`). Copying the CSRF cookie into a header alone is insufficient protection. Logout is POST-only.
- Keep `content-encoding` and `content-length` out of forwarded upstream response headers: Node fetch decodes the body but retains headers describing compressed bytes. Passing those headers caused a real brotli/gzip outage.
- Update `userReferences` and `userDependencies` in `queries/index.ts` when adding user-specific queries. User changes, including changes in another tab, must reset personalized queries; logout errors must be visible.
- Browser queries default to 60 seconds of freshness; categories/pages never go stale, products stay fresh for ten minutes. Avoid `initialData: []` for lists not yet loaded: it suppresses fetching during staleTime. Use a module-level empty constant as the destructuring default.
- Django omits null, empty-string and empty-list fields; guard optional data such as product images with `?? []` even if an older type says it is required. `ta=1` product suggestions return title strings. Empty `ordering=` retains backend relevance ordering; `variations=` means no variations.
- Product filters are objects serialized with `productSearchParams`, not legacy `{field, value}[]` arrays. Preserve the backend filter metadata contract (`class`, `widget`, `choices`, `attrs.step/min_value/max_value`). `fields=` is for selective API reads, not catalog URL state.
- Display-price filtering/sorting uses `cost` (discounts included). Retain `price` in the API contract and the sitemap/XML bounds `price: [0, 10000000]`. Cartzilla's search uses Diginetica; do not fold it into backend filter changes.

## Static generation and revalidation

- Keep the existing fetch-tag caching model; a Cache Components migration was not part of this design.
- `generateStaticParams` enumerates entities only when `NODE_ENV === 'production'` and `PLAYWRIGHT_TEST !== 'true'`; otherwise return `[]`. New content pages under `/pages/[...uri]` must render on demand after the build.
- Loaders used by static pages attach `tagged(...)` from `src/lib/queries/cache-tags.ts`. Keep these tags aligned with `../django-shop/shop/revalidation.py`; a new data dependency needs matching invalidation on both sides.
- `/api/revalidate` accepts `{ secret, tags, background? }`, with `secret` matching `REVALIDATION_TOKEN`. Legacy `{model, pk}` payloads are unsupported. Immediate expiry uses `{ expire: 0 }`; background revalidation uses `'max'`.
- Admin edits and price changes expire immediately. Stock changes revalidate in the background only when displayed availability changes (0 / 1 / >1 / >5 / whole pack). Batch import changes rather than invalidating per product indiscriminately.
- Do not tag whole-catalog sitemap/feed lists by every product; use `productListTags()` for category/home dependencies. Fallbacks are hourly for home, catalog, products and feeds; daily for actions, stores, service centers, content pages and sitemap. The old forum remains static.
- Staff GET `/api/revalidate/?path=/catalog/sewing/` or `?all` authenticates via Django `is_staff`, revalidates and redirects with 303. A URL prefix is not a route-file subtree; only a single page or the root layout can be targeted this way.
- Verify caching against a production build; `next dev` does not exercise production page caching.

## UI and shared storefront code

- Use inline Tailwind utilities and existing `src/components/ui/` helpers. `src/styles.css` owns Cartzilla theme tokens and scans `src/` only. Breakpoints match Tailwind defaults and `src/lib/breakpoint.ts`.
- Prefer named exports for new UI parts and shared Base UI wrappers. There is no tailwind-merge: add helper options instead of conflicting padding, positioning or display classes. Icons normally use Tabler with `stroke={1.5}`.
- Keep crawlable Collapsible links mounted. Preserve `.sw-shown-md`/`.sw-shown-lg` handling of `[hidden]`. Base UI Autocomplete's hidden input can prevent Enter submission when a form lacks a submit button; keep the mobile search's visually hidden submit button.
- Swiper CSS is unlayered, so display utilities on its root/slides need `!`. Reserve space for pagination; a layout shift between pointerdown and pointerup can close a Base UI menu, especially in Mobile Safari.
- Backend HTML uses `contentClass()`/`advertClass` in `ui/content.ts`. Keep `backend-content.css` scoped to `.backend-content` until the backend HTML conversion is verified. `backend-safelist.css` must match the output of django-shop's `manage.py tailwindize_html` across storefronts.
- HTML conversion is dry-run by default; never run `--write` against the local `sworld` database. Test on a disposable copy, preserve embedded `<style>` classes, and check second-pass idempotency. Only after conversion should the Bootstrap compatibility CSS and marker be removed.
- Shared code is copied between cartzilla, janome.club, singer.ru, dor-tak.ru and familysew.ru; this is not a shared-package architecture. Keep `src/lib/`, the API proxy and revalidation route aligned across all five, and XML feed logic aligned where feeds exist. Shared dependency versions follow Cartzilla when syncing.
- The first four storefronts also share user-flow files: user login/register/update/confirm-email forms, phone-code-input, profile/sidebar/topbar/avatar; order confirmation/details/list/payment-button/status-badge; cart contents/item; countdown; product/product-link. Familysew has no login and does not share these components.
- Site differences belong in `src/storefront.ts` (favorites, productPages, productFilters), each site's UI helpers and theme tokens. Backend properties belong in `useSite()`, e.g. `wholesale` for whole packs. Orders are filtered by site. Shared components must not acquire brand-specific branches.
- Shared helpers retain Cartzilla's API; retain `text-h1`–`text-h6`, `text-ms`, `text-md`, `text-heading`, `text-link-hover`, `text-overlap` and `pb-overlap`. Carry new shared helper options/tokens to the consuming storefronts during coordinated changes. Their pages, header cart and branding remain site-specific.

## Feeds, builds and deployment

- `src/app/xml/[filename]/route.ts` renders EJS templates from `templates/xml/`. `products` and `search` are global feeds; other names identify an integration UTM and its `output_template`. Tokenized queries are server-only. Docker mounts `templates/` as a volume.
- `.github/workflows/frontend.yml` is the current authority: pushes to `sworld` run lint/types, then tests and image build independently. Stage deployment depends on the build, **not** the test job.
- Images are `ghcr.io/andreynovikov/sworld:latest` and `<commit-date-in-Europe/Moscow>-<7-char-sha>`. There are no package versions or release tags. Stage uses port 4004; production uses 4104.
- Production deployment is a user-run workflow dispatch on `sworld`, deploying the already-built commit image. Re-running an earlier deployment rolls back. Do not treat a successful build as authorization to deploy production.
- Build and test jobs read `ENV_FILE` from the `sworld` GitHub environment; the production `.env` is baked into the image and stage uses that image. Changing a secret requires a new build, not merely another deploy. Deploy secrets include `DEPLOY_HOST`, `DEPLOY_HOST_KEY`, `DEPLOY_USER`, `SSH_PRIVATE_KEY`; preserve pinned SSH host-key checking.
- `startup.sh` copies static/public assets into `.docker/` before pruning old files, keeping `public/unavailable.html` available to nginx, then execs Node for proper shutdown. Preserve `lazyWithReload` for deferred product stock/reviews chunks; it limits recovery reloads to once per minute via sessionStorage.
- For server configuration, consult `deploy/README.md` and `deploy/ansible/` on `main`. Do not infer live deployment state from old Claude rollout notes.

## Known follow-ups and deliberate limits

- Cookie transition cleanup is **not before 2026-12-07**, four weeks after the recorded rename. Before doing it, verify deployment timing. Remove legacy `'csrftoken'` from `CSRF_COOKIES` across five storefronts and coordinate Django's `CookieRenameMiddleware`, `'sessionid'` fallback, tests and comments. Local `PROBLEMS.md` has the checklist; it is gitignored and may be absent in another clone. Deployment of Django's POST-only logout was still listed there as pending; verify rather than assuming it is live.
- Preserve chosen account behavior: SMS-verified two-step registration/phone changes; silent checkout/preorder/warranty accounts remain unverified; eight-character minimum passwords without complexity rules; wrong-password throttling must not block SMS login. Taken-email disclosure requires a correct SMS code, except the documented signed-in profile flow. Own order mail waits for email confirmation (up to seven days); staff edits count as confirmed.
- Deliberate security limits in `PROBLEMS.md`: no API-path allowlist or captcha; limited phone/username enumeration remains; external receipt/delivery/analytics systems may receive unconfirmed emails; abandoned-basket links use sewing-world.ru. Full CSP was deferred; preserve Metrika-compatible frame ancestors and DENY on auth/account pages. Legacy duplicate-phone accounts require staff handling. Do not silently change these product decisions during unrelated work.
- Cost rollout notes leave category filter/order SQL to the user after frontend deployment; completion is unverified. The backend still lists both price and cost search facets pending coordinated cleanup. Do not execute that data change as routine setup.
- `public/unavailable.html` exists, but live nginx mapping of 502/503/504 to 503 with Retry-After/no-store was left to the user; verify server configuration before claiming it is deployed.
- A Firefox CSS HMR problem was reported on an older Next version: server updates arrived but the tab did not apply them; no browser-side cause was established. Reproduce on current dependencies before changing code. Tailwind accumulates classes until restart, and error pages force reloads, so use fresh classes and a healthy page when probing.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
