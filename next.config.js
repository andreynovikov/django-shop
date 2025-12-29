module.exports = {
    reactStrictMode: true,
    trailingSlash: true,
    output: 'standalone',
    images: {
        remotePatterns: [
        new URL('https://api.sewing-world.ru/media/**'),
        new URL('https://www.sewing-world.ru/media/**'),
        ],
    },
}
