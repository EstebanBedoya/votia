import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Pixel-art assets must be served byte-for-byte: the Next image optimizer
  // (/_next/image) both resamples sprites — blurring them — and fails in the
  // alpine standalone runtime where sharp isn't available. Serve raw files.
  // Sprites are hosted on public Supabase Storage, so allow that remote host.
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.supabase.co",
        pathname: "/storage/v1/object/public/**",
      },
    ],
  },
};

export default nextConfig;
