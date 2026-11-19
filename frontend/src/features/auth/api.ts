import { apiRequest } from "@/lib/api/client";
import type { AuthUser, LoginInput, TokenPair } from "@/lib/auth/types";

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

export async function loginWithBff(input: LoginInput): Promise<{
  access_token: string;
  expires_in: number;
}> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
    credentials: "include",
  });

  const payload = (await response.json()) as {
    access_token?: string;
    expires_in?: number;
    message?: string;
  };

  if (!response.ok || !payload.access_token) {
    throw new Error(payload.message ?? "Login failed");
  }

  return {
    access_token: payload.access_token,
    expires_in: payload.expires_in ?? 3600,
  };
}

export async function logoutWithBff(accessToken: string | null): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    headers: {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    credentials: "include",
  });
}

export async function refreshTokensDirect(
  refreshToken: string,
): Promise<TokenPair> {
  return apiRequest<TokenPair>("/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
    auth: false,
  });
}