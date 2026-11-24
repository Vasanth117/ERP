import type { NextConfig } from "next";

const apiUrl = process.env.NEXT_PUBLIC_API_URL;
const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX;

if (process.env.VERCEL === "1") {
  if (!apiUrl || apiUrl.includes("localhost")) {
    throw new Error(
      "NEXT_PUBLIC_API_URL must be set to your production API (e.g. Render) in Vercel → Environment Variables as a plain project variable, then redeploy.",
    );
  }
}

const nextConfig: NextConfig = {
  env: {
    ...(apiUrl ? { NEXT_PUBLIC_API_URL: apiUrl } : {}),
    ...(apiPrefix ? { NEXT_PUBLIC_API_PREFIX: apiPrefix } : {}),
  },
};

export default nextConfig;
