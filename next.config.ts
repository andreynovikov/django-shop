import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  trailingSlash: true,
  output: 'standalone',
  allowedDevOrigins: ['singer.ru'],
  images: {
    remotePatterns: [
      new URL('https://api.sewing-world.ru/media/**'),
      new URL('https://www.sewing-world.ru/media/**'),
    ],
  },
  async headers() {
    return [
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
  sassOptions: {
    silenceDeprecations: ['import', 'if-function']
  },
  logging: {
    browserToTerminal: true,
  },
}

export default nextConfig;
