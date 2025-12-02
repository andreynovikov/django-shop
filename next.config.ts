import type { NextConfig } from "next";

const regexEqual = (x: RegExp, y: RegExp) => {
    return (
        x instanceof RegExp &&
        y instanceof RegExp &&
        x.source === y.source &&
        x.global === y.global &&
        x.ignoreCase === y.ignoreCase &&
        x.multiline === y.multiline
    )
}

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
  webpack: config => { // https://github.com/vercel/next.js/issues/71638 (sassOptions)
    const oneOf = config.module.rules.find(
      // @ts-expect-error format of webpack config is not typed
      rule => typeof rule.oneOf === 'object'
    )

    if (oneOf) {
      // @ts-expect-error format of webpack config is not typed
      const sassRule = oneOf.oneOf.find(rule => regexEqual(rule.test, /\.module\.(scss|sass)$/))
      if (sassRule) {
        const sassLoader = sassRule.use.find(
          // @ts-expect-error format of webpack config is not typed
          el => el.loader.includes('next/dist/compiled/sass-loader')
        )
        if (sassLoader) {
          sassLoader.loader = 'sass-loader'
        }
      }
    }

    return config
  },
  sassOptions: {
    silenceDeprecations: ['import']
  }
}

export default nextConfig;