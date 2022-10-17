module.exports = {
    reactStrictMode: true,
    trailingSlash: true,
    distDir: process.env.BUILD_DIR || '.next',
    async rewrites() {
        return [
            {
                source: '/api/v0/:path*/',
                destination: 'http://127.0.0.1:8000/api/v0/:path*/' // Proxy to Backend
            }
        ]
    }
}
