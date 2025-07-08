/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    trailingSlash: true,
    output: 'standalone',
    async redirects() {
        return [
            {
                source: '/blog',
                destination: '/blog/entries',
                permanent: true
            },
        ]
    }
}

export default nextConfig;