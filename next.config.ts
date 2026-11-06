import type { NextConfig } from "next";

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
  async headers() {
    return [
      {
        source: '/cart',
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
