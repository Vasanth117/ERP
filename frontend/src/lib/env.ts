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

export function apiBaseUrl(): string {
  const base = publicEnv.apiUrl.replace(/\/$/, "");
  const prefix = publicEnv.apiPrefix.startsWith("/")
    ? publicEnv.apiPrefix
    : `/${publicEnv.apiPrefix}`;
  return `${base}${prefix}`;
}