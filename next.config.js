module.exports = {
    reactStrictMode: true,
    trailingSlash: true,
    output: 'standalone',
    distDir: process.env.BUILD_DIR || '.next'
}
