/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow the app to be deployed to any domain
  output: 'standalone',
  // Silence ESLint during builds (lint separately)
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
}

module.exports = nextConfig
