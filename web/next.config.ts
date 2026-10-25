import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  experimental: {
    agentUpgrade: "security",
    serverActions: {
      bodySizeLimit: "1mb",
    },
  },
}

export default nextConfig
