import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  trailingSlash: true,
  output: 'standalone',
  images: {
    remotePatterns: [
      new URL('https://api.sewing-world.ru/media/**'),
      new URL('https://www.sewing-world.ru/media/**'),
    ],
  },
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
  sassOptions: {
    silenceDeprecations: ['import', 'if-function']
  }
}

export default nextConfig;