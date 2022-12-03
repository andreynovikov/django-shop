const path = require('path');

module.exports = {
    reactStrictMode: true,
    trailingSlash: true,
    output: 'standalone',
    distDir: process.env.BUILD_DIR || '.next',
    sassOptions: {
        includePaths: [path.join(__dirname, 'src/vendor/sell/scss')],
    }
}
