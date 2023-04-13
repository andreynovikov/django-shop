const path = require('path');

module.exports = {
    reactStrictMode: true,
    trailingSlash: true,
    output: 'standalone',
    sassOptions: {
        includePaths: [path.join(__dirname, 'src/vendor/sell/scss')],
    }
}
