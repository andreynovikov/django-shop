# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Next.js storefront for sewing-world.ru (package name `sworld`, branch `cartzilla`), styled with Tailwind CSS v4 after the look of the Cartzilla theme it was built on. It has no database of its own: all data comes from a separate Django backend (the `django-shop` repo) over REST at `${API_SERVER}/api/v0/`. The UI and content are in Russian.

## Commands

- `npm run dev`: dev server at https://127.0.0.1:3004 (experimental HTTPS). It uses the certs in `certificates/`, which is gitignored. On a fresh clone, create them first with `mkcert -install -key-file certificates/localhost-key.pem -cert-file certificates/localhost.pem localhost 127.0.0.1 ::1`. The certs are passed explicitly because Next's own reuse check fails for an IP host and would regenerate them on every start.
- `npm run test`: plain `next dev` at http://127.0.0.1:4004. Playwright uses this as its web server locally.
- `npm run build` / `npm start`: production build (`output: 'standalone'`) and server on port 4004
- `npm run lint`: ESLint over `src/` (next core-web-vitals, next typescript, and the tanstack-query recommended rules)
- `npm run test:e2e`: Playwright tests in `tests/` (chromium, firefox, Mobile Chrome)
  - Run one file: `npx playwright test tests/checkout.spec.ts`
  - Run one test by name: `npx playwright test -g "anonymous buyer orders"`
  - Run one browser: `npx playwright test --project=chromium`
  - The tests read from the real backend configured in `.env`. With `CI` set, they run against `node .next/standalone/server.js` instead of the dev server.
  - Tests must never write to that backend. The auto fixture `blockApiWrites` in `tests/fixtures.ts` aborts every non-GET `/api/v0/` request that no test mocked, and fails the test.
  - User flows (login, registration, cart, orders, favorites, profile, warranty) use the `backend` fixture: `tests/fake-backend.ts`, an in-memory copy of django-shop's user endpoints with a session, a basket, favorites, orders, serial number registration and an SMS log. It answers browser requests only, which is enough because user state is never rendered on the server. Requests it does not handle fall through to the real backend (GET) or the guard. Seed state with `backend.addUser()`, `backend.signIn()`, `backend.addOrder()` and `backend.addFavorites()`, and read the code a login sent with `backend.lastSmsCode(phone)`.
  - Contract checks (`tests/contract.ts`) validate every request the fake answers, and every fake answer, against the backend's OpenAPI schema; a mismatch fails the test. Global setup downloads the schema from `${API_SERVER}/api/v0/schema/` with `API_TOKEN` into `tests/.cache/openapi.json` and reuses it for an hour (delete the file to refresh). Set `API_SCHEMA` to a local schema file, e.g. from django-shop's `manage.py spectacular --format openapi-json`, to check backend changes before deploying them.

Required `.env` variables: `API_SERVER`, `API_TOKEN`, `ORIGIN`, `NEXT_PUBLIC_YMAPS_API_KEY`, the `NEXT_PUBLIC_*_VERIFICATION` variables, and `REVALIDATION_TOKEN` (used by `/api/revalidate`).

## Architecture

### App Router
Everything is in `src/app/`. The route groups `(auth)` (login, registration), `(pages)` (service centers, stores, warranty) and `(shop)` (catalog, products, search, cart, compare, checkout) only sort the files. Beside them are `user/` (account pages, noindex via `user/layout.tsx`), `blog/`, `actions/`, `pages/[...uri]` (content pages), `oldforum/`, `sitemap.ts`, the API proxy, `api/revalidate` and the XML feeds.
- The root `layout.tsx` loads the catalog and renders the topbar, bottom bar and handheld toolbar around every page. `providers.tsx` sets up TanStack Query, nuqs, the site, navigation, the session, toasts, and the topbar and toolbar contexts.
- Page headers come from the hook-free `pageContentWrapper()` (`src/components/layout/page-content-wrapper.tsx`), so server components can render them. It combines `PageHeader` (the frame) and `PageTitle` (breadcrumbs and `h1`), which a layout can also use separately.
- Account pages share `user/layout.tsx`, which holds the header frame and the sidebar. Each page's title, breadcrumbs and metadata are in the `@header` slot, in a page at the same path (`user/@header/orders/[id]/page.tsx` next to `user/orders/[id]/page.tsx`), so a new account page needs both files. The sidebar stays mounted between account pages, so its state carries over.
- User data (session, basket, favorites, comparisons, orders) is loaded in the browser only, so the pages that show it stay static. Components that read the query (`/search`, `/compare`, `/user/orders`, category filters) use nuqs inside a Suspense boundary: the route's `loading.tsx`, or a `<Suspense>` around the component when the header must stay out of the fallback. A header that should show while a page loads goes in the segment's `layout.tsx`, outside the `loading.tsx` boundary (see `/products/[code]`, `/compare`).
- Client components use `next/navigation` directly: `useRouter()` to navigate and `usePathname()` for the path. `useSearchParams()` (and nuqs) needs a Suspense boundary in static routes. Keep each boundary around just the part that renders from the query, with a fallback that renders it without the query, so the rest of the page stays in the static HTML (see `RegisterLink` in `login-form.tsx` and `CurrentCatalog`). Event handlers read the URL from `window.location` instead of a hook.

### Data layer (`src/lib/queries/`)
- Each resource module exports a query-key factory (`xxxKeys`) and plain `load*`/`retrieve*` functions built on `apiFetch` (`fetch.ts`). Everything is re-exported from `@/lib/queries`.
- `apiFetch` sends requests with a body to the relative `/api/v0/...` path. That path is the proxy `src/app/api/v0/[...path]/route.ts`, which forwards cookies, sets Django's `X-CSRFToken` header from the `csrftoken` cookie, and passes `Set-Cookie` back. Requests without a body are prefixed with `API_SERVER`. `API_SERVER` isn't `NEXT_PUBLIC_`, so it is set only on the server. As a result, server-side GETs go straight to Django (with an `origin: ORIGIN` header), and every browser request goes through the proxy. The proxy exports only GET, POST and PUT.
- `API_TOKEN` (`queries/tokenized.ts`) is used only in server code (the XML feeds).
- `userReferences` and `userDependencies` in `queries/index.ts` list the queries that are reset or invalidated on login and logout. Update them when you add user-specific queries.
- `src/lib/query-client.ts` sets the default `staleTime` to 60 s; categories and pages never go stale, products stay fresh for 10 minutes. Because of the default, `initialData` counts as fresh and the query is not fetched for a minute, even when it becomes enabled later. For a list that is empty until loaded, use a module-level empty constant as the destructuring default instead (see `useComparison` and `useFavorites`).
- Shared types are in `src/lib/types.ts`. Cross-cutting hooks and contexts are in `src/lib/`: `useSite`, `useSession`, `useBasket`, favorites, comparison, topbar/toolbar.

### Static generation and revalidation
- `generateStaticParams` pre-renders every entity only when `NODE_ENV === 'production'` and `PLAYWRIGHT_TEST !== 'true'`; otherwise it returns `[]`, and each page is rendered on its first request and cached (most set `export const revalidate = 3600`). CI sets `PLAYWRIGHT_TEST=true` so the build stays fast. Follow the same guard in new static routes.
- The Django backend POSTs saved model items to `/api/revalidate` (`src/app/api/revalidate/route.ts`) with `REVALIDATION_TOKEN`. The handler calls `revalidatePath()` for each item's page, which is then rendered again on its next visit. When you add a model whose pages need revalidating, map it to its path in `getPathForModelItem`.

### XML feeds
`src/app/xml/[filename]/route.ts` serves product feeds such as `/xml/market.xml`. It renders the EJS templates in `templates/xml/`. `products` and `search` are global feeds. Any other filename is treated as an integration UTM, looked up on the backend, and rendered with that integration's `output_template`. In Docker, `templates/` is mounted as a volume.

### Styling
- Tailwind CSS v4 through `@tailwindcss/postcss`. `src/styles.css` holds the theme: Cartzilla's colors and grays, the `text-h1`–`text-h6` heading sizes, `text-ms`/`text-md`, radii, shadows and the `container`. It scans only `src/` (`source('.')`). The base layer adds link and heading colors, inline Tabler icons and `.sw-shown-md`/`.sw-shown-lg` for `keepMounted` Collapsible panels that stay shown from a breakpoint up, which preflight's `[hidden]` would hide.
- Breakpoints are Tailwind's defaults; `lib/breakpoint.ts` has the same values.
- Components use utilities inline. Repeated Cartzilla patterns are class helpers in `src/components/ui/`: `buttonClass`, the form classes, `Alert`, `badgeClass`, card, menu, nav, widget, navbar tool and handheld toolbar classes, `carouselNavClass`, slider classes, and the Base UI wrappers (modal, offcanvas, tooltip, autocomplete). There is no tailwind-merge: don't add a class that sets what a helper already sets (e.g. a second `px-*` or display), add a helper option instead.
- Icons are Tabler (`@tabler/icons-react`), usually `stroke={1.5}`.
- Swiper's CSS is unlayered, so display utilities on slides and on the Swiper root need `!`.
- HTML from the backend (product texts, pages, blog, actions, stores) goes into `contentClass()` from `ui/content.ts`: the typography plugin's `prose`, tuned to Cartzilla's spacing. Adverts get `advertClass`.
- The stored HTML still has Bootstrap classes. `src/backend-content.css` styles the ones it uses, scoped to `.backend-content`, until django-shop's `manage.py tailwindize_html --write` converts them; then delete it and remove `backend-content` from the content classes (see `shop/tailwind_html.py` in django-shop). `src/backend-safelist.css`, printed by that command and identical in every storefront, makes Tailwind generate the classes of the converted HTML.
- The Playwright tests select by role, label and text.

## Release and deploy
- The version in `package.json` uses the format `YYYY.MM.DD`. Release commits are named `vYYYY.MM.DD` and tagged with the same name.
- `.github/workflows/frontend.yml`: every push to `cartzilla` builds a Docker image, pushes it to GHCR, and deploys it to stage on port 4004. A `v*` tag also deploys it to production on port 4104.
- At container start, `startup.sh` copies `.next/static` and `public/` into the `.docker/` volume so nginx can serve them.
- `DEPLOYMENT.rst` documents the server setup: nginx, Postgres, the Django backend, and replication.
