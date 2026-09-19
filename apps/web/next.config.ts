import path from "node:path";
import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

// ADR-004: service worker generated at build time (webpack plugin), off in dev.
const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
});

const nextConfig: NextConfig = {
  // Docker runtime: `node apps/web/server.js` from .next/standalone (monorepo-aware tracing).
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default withSerwist(nextConfig);
