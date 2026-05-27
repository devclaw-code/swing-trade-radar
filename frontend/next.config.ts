import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow remote browsers (Azure VM public IP) to load dev HMR resources.
  allowedDevOrigins: ["4.154.152.152", "*.cloudapp.azure.com", "10.0.0.4"],

  // Proxy /api/* to the FastAPI backend so the browser only needs :8080.
  // Override with BACKEND_URL env var if running elsewhere.
  async rewrites() {
    const target = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${target}/api/:path*` }];
  },
};

export default nextConfig;
