import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // Allow components to be imported without "use client" for SSR
  },
};

export default nextConfig;
