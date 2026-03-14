/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ensure better-sqlite3 native module is not bundled by webpack
  serverExternalPackages: ['better-sqlite3'],
  // Silence ESLint during builds (lint separately)
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
}

module.exports = nextConfig
