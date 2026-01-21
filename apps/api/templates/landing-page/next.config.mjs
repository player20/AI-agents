/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // WebContainer compatibility - disable native SWC
  experimental: {
    forceSwcTransforms: true,
  },
  swcMinify: false,
}

export default nextConfig
