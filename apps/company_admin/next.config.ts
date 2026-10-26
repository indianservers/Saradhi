import type { NextConfig } from "next";
const config: NextConfig = {
  transpilePackages: ["@quickbuddy/sdk", "@quickbuddy/web-design-system"],
  poweredByHeader: false,
  async headers() { return [{ source: "/(.*)", headers: [
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    { key: "X-Frame-Options", value: "DENY" }
  ] }]; }
};
export default config;
