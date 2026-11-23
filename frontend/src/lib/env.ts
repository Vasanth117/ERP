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

/** BFF `/api/auth/*` on same origin; disabled when API is remote (e.g. Vercel → Render). */
export function useBffAuth(): boolean {
  const override = process.env.NEXT_PUBLIC_USE_BFF_AUTH?.trim();
  if (override === "1" || override === "true") return true;
  if (override === "0" || override === "false") return false;
  const api = publicEnv.apiUrl.toLowerCase();
  return api.includes("localhost") || api.includes("127.0.0.1");
}

export function apiBaseUrl(): string {
  const base = publicEnv.apiUrl.replace(/\/$/, "");
  const prefix = publicEnv.apiPrefix.startsWith("/")
    ? publicEnv.apiPrefix
    : `/${publicEnv.apiPrefix}`;
  return `${base}${prefix}`;
}