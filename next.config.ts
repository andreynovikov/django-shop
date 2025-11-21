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
      {
        source: '/blog',
        destination: '/blog/entries',
        permanent: true
      },
    ]
  },
}

export default nextConfig;