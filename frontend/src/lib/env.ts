function requirePublicEnv(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`Missing environment variable: ${name}`);
  }
  return value;
}

export const publicEnv = {
  apiUrl: requirePublicEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000"),
  apiPrefix: requirePublicEnv("NEXT_PUBLIC_API_PREFIX", "/api/v1"),
} as const;

/** BFF `/api/auth/*` on same origin — only for local dev (localhost frontend + local API). */
export function useBffAuth(): boolean {
  const override = process.env.NEXT_PUBLIC_USE_BFF_AUTH?.trim();
  if (override === "1" || override === "true") return true;
  if (override === "0" || override === "false") return false;

  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1") {
      // Deployed: browser → same-origin BFF; Vercel Functions read API URL at runtime.
      return true;
    }
  }

  const api = publicEnv.apiUrl.toLowerCase();
  return api.includes("localhost") || api.includes("127.0.0.1");
}

/** Fail fast when a Vercel build was produced without NEXT_PUBLIC_API_URL. */
export function assertRemoteApiConfigured(): void {
  if (typeof window === "undefined") return;
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return;
  const api = publicEnv.apiUrl.toLowerCase();
  if (api.includes("localhost") || api.includes("127.0.0.1")) {
    throw new Error(
      "Set NEXT_PUBLIC_API_URL to your Render URL in Vercel → Environment Variables, then redeploy (build must include the variable).",
    );
  }
}

export function apiBaseUrl(): string {
  const base = publicEnv.apiUrl.replace(/\/$/, "");
  const prefix = publicEnv.apiPrefix.startsWith("/")
    ? publicEnv.apiPrefix
    : `/${publicEnv.apiPrefix}`;
  return `${base}${prefix}`;
}