# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Next.js storefront for sewing-world.ru (package name `sworld`, branch `cartzilla`), built on the Cartzilla Bootstrap theme. It has no database of its own: all data comes from a separate Django backend (the `django-shop` repo) over REST at `${API_SERVER}/api/v0/`. The UI and content are in Russian.

## Commands

- `npm run dev`: dev server at https://127.0.0.1:3004 (experimental HTTPS; certs live in `certificates/`)
- `npm run test`: plain `next dev` at http://127.0.0.1:4004. Playwright uses this as its web server locally.
- `npm run build` / `npm start`: production build (`output: 'standalone'`) and server on port 4004
- `npm run lint`: ESLint over `src/` (next core-web-vitals, next typescript, and the tanstack-query recommended rules; `src/vendor/` is ignored)
- `npm run test:e2e`: Playwright tests in `tests/` (chromium, firefox, Mobile Chrome)
  - Run one file: `npx playwright test tests/cart.spec.ts`
  - Run one test by name: `npx playwright test -g "product can be put in cart"`
  - Run one browser: `npx playwright test --project=chromium`
  - The tests hit the real backend configured in `.env`. With `CI` set, they run against `node .next/standalone/server.js` instead of the dev server.

Required `.env` variables: `API_SERVER`, `API_TOKEN`, `ORIGIN`, `NEXT_PUBLIC_YMAPS_API_KEY`, the `NEXT_PUBLIC_*_VERIFICATION` variables, and `REVALIDATION_TOKEN` (used by `/api/revalidate`).

## Architecture

### Two routers during migration
The app is moving from the Pages Router to the App Router, and both are live:
- `src/pages/`: most pages. They use `getStaticProps`/`getStaticPaths` (ISR with `fallback: 'blocking'`) or `getServerSideProps`, and pass prefetched TanStack Query state to the client as `dehydratedState`. Per-page layouts use the `Component.getLayout` pattern defined in `src/pages/_app.tsx`.
- `src/app/`: the root layout and providers (`layout.tsx`, `providers.tsx`), auth pages (`(auth)/login`, `(auth)/register`), `sitemap.ts`, the API proxy, and the XML feeds.
- `src/pages/_app.tsx` and `src/app/providers.tsx` set up the same provider tree and moment `ru` locale overrides. Change both together.
- `src/lib/navigation/` holds a temporary `useNavigation()` abstraction that has a `PagesNavigationProvider` and an `AppNavigationProvider`. Use it in shared components instead of `next/router` or `next/navigation`, so they work under either router.

### Data layer (`src/lib/queries/`)
- Each resource module exports a query-key factory (`xxxKeys`) and plain `load*`/`retrieve*` functions built on `apiFetch` (`fetch.ts`). Everything is re-exported from `@/lib/queries`.
- `apiFetch` sends requests with a body to the relative `/api/v0/...` path. That path is the proxy `src/app/api/v0/[...path]/route.ts`, which forwards cookies, sets Django's `X-CSRFToken` header from the `csrftoken` cookie, and passes `Set-Cookie` back. Requests without a body are prefixed with `API_SERVER`. `API_SERVER` isn't `NEXT_PUBLIC_`, so it is set only on the server. As a result, server-side GETs go straight to Django (with an `origin: ORIGIN` header), and every browser request goes through the proxy. The proxy exports only GET, POST and PUT.
- `API_TOKEN` (`queries/tokenized.ts`) is used only in server code (the XML feeds).
- `userReferences` and `userDependencies` in `queries/index.ts` list the queries that are reset or invalidated on login and logout. Update them when you add user-specific queries.
- Default `staleTime` is set per key family in the providers: categories and pages never go stale, products stay fresh for 10 minutes.
- Shared types are in `src/lib/types.ts`. Cross-cutting hooks and contexts are in `src/lib/`: `useSite`, `useSession`, `useBasket`, favorites, comparison, topbar/toolbar.

### Static generation and revalidation
- `getStaticPaths` pre-renders every entity only when `NODE_ENV === 'production'` and `PLAYWRIGHT_TEST !== 'true'`. CI sets `PLAYWRIGHT_TEST=true` so the build stays fast. Follow the same guard in new static routes.
- The Django backend calls `POST /api/revalidate` (`src/pages/api/revalidate.ts`) with `REVALIDATION_TOKEN` to trigger on-demand ISR. When you add a model whose pages need revalidating, map it to its path in `getPathForModelItem`.

### XML feeds
`src/app/xml/[filename]/route.ts` serves product feeds such as `/xml/market.xml`. It renders the EJS templates in `templates/xml/`. `products` and `search` are global feeds. Any other filename is treated as an integration UTM, looked up on the backend, and rendered with that integration's `output_template`. In Docker, `templates/` is mounted as a volume.

### Styling
`src/styles.scss` imports the vendored Cartzilla theme (`src/vendor/cartzilla/scss`, built on the vendored Bootstrap in `src/vendor/bootstrap`) and adds the site's own tweaks. Components use react-bootstrap plus the Cartzilla CSS classes. The Playwright selectors depend on those classes, e.g. `.navbar-tool-label` and `.ci-cart`. Don't edit files under `src/vendor/`.

## Release and deploy
- The version in `package.json` uses the format `YYYY.MM.DD`. Release commits are named `vYYYY.MM.DD` and tagged with the same name.
- `.github/workflows/frontend.yml`: every push to `cartzilla` builds a Docker image, pushes it to GHCR, and deploys it to stage on port 4004. A `v*` tag also deploys it to production on port 4104.
- At container start, `startup.sh` copies `.next/static` and `public/` into the `.docker/` volume so nginx can serve them.
- `DEPLOYMENT.rst` documents the server setup: nginx, Postgres, the Django backend, and replication.
