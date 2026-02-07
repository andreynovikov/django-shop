const path = require('path');

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
    sassOptions: {
        //includePaths: [path.join(__dirname, 'src/vendor/sell/scss')],
    }
}
