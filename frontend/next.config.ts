/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Ignore lint errors during build (safe for deploy)
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;