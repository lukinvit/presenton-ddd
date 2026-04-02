/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.GATEWAY_URL || 'http://localhost:8000'}/api/v1/:path*`,
      },
    ];
  },
  images: {
    domains: ['localhost'],
  },
};

export default nextConfig;
