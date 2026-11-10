import type { NextConfig } from "next";

// Metrika's Webvisor and click maps show the pages in a frame on its own sites. The list is from its help,
// https://yandex.ru/support/metrica/code/install-counter-csp.html ("Адреса для frame-ancestors").
const METRIKA_FRAME_ANCESTORS = [
  'metrika.yandex.ru', 'analytics.yandex.by', 'analytics.yandex.com', 'analytics.yandex.com.tr', 'analytics.yandex.kz',
  'analytics.yandex.ru', 'metr.yandex.by', 'metr.yandex.com', 'metr.yandex.com.tr', 'metr.yandex.kz', 'metr.yandex.ru',
  'metrica.ya.ru', 'metrica.yandex', 'metrica.yandex.by', 'metrica.yandex.com', 'metrica.yandex.com.tr', 'metrica.yandex.kz',
  'metrica.yandex.ru', 'metrika.ya.ru', 'metrika.yandex', 'metrika.yandex.by', 'metrika.yandex.com', 'metrika.yandex.com.tr',
  'metrika.yandex.kz', 'metrika.yandex.uz',
].map(host => `https://${host}`)

// Pages that sign in or change the account, where a click in a hidden frame would act for the user
const UNFRAMED_PAGES = ['/login', '/register', '/confirm-email', '/user/:path*']

const nextConfig: NextConfig = {
  reactStrictMode: true,
  trailingSlash: true,
  output: 'standalone',
  images: {
    remotePatterns: [
      new URL('https://api.sewing-world.ru/media/**'),
      new URL('https://www.sewing-world.ru/media/**'),
      // Media URLs are built from the backend host, e.g. a local Django in development
      ...(process.env.API_SERVER ? [new URL(`${process.env.API_SERVER}/media/**`)] : []),
    ],
  },
  staticPageGenerationTimeout: 240, // sitemap is generated very slow
  async redirects() {
    return [
      // restructure
      {
        source: '/blog',
        destination: '/blog/entries',
        permanent: true
      },
      // ancient links
      {
        source: '/index.html',
        destination: '/',
        permanent: true
      },
      {
        source: '/articles/sewingmachines/(:?index\.html)?',
        destination: '/blog/Q/',
        permanent: true
      },
      {
        source: '/articles/embroidery/index.html',
        destination: '/blog/R/',
        permanent: true
      },
      {
        source: '/articles/serger/index.html',
        destination: '/blog/S/',
        permanent: true
      },
      {
        source: '/articles/serger/tension.html',
        destination: '/blog/T/',
        permanent: true
      },
      {
        source: '/articles/embroidery/',
        destination: '/blog/R/',
        permanent: true
      },
      {
        source: '/articles/serger/',
        destination: '/blog/S/',
        permanent: true
      },
    ]
  },
  async headers() {
    return [
      // Only this site and Metrika may show the pages in a frame. A later entry overrides a header of an earlier one.
      {
        source: '/:path*',
        headers: [
          { key: 'Content-Security-Policy', value: ["frame-ancestors 'self'", ...METRIKA_FRAME_ANCESTORS].join(' ') },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
        ],
      },
      ...UNFRAMED_PAGES.map(source => ({
        source,
        headers: [
          { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
          { key: 'X-Frame-Options', value: 'DENY' },
        ],
      })),
      {
        source: '/cart',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/compare',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/confirmation',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/search',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/user/:path*',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
    ]
  },
  logging: {
    browserToTerminal: true,
  },
}

export default nextConfig;
