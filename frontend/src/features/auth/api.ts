import { apiRequest } from "@/lib/api/client";
import { parseResponseJson } from "@/lib/api/parse-response-body";
import { useBffAuth } from "@/lib/env";
import {
  clearRefreshToken,
  clearAccessToken,
  setRefreshToken,
} from "@/lib/auth/token-store";
import {
  clearSessionIndicatorCookie,
  setSessionIndicatorCookie,
} from "@/lib/auth/session-client";
import type { AuthUser, LoginInput, TokenPair } from "@/lib/auth/types";

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

async function loginViaBff(input: LoginInput): Promise<{
  access_token: string;
  expires_in: number;
} | null> {
  let response: Response;
  try {
    response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      credentials: "include",
    });
  } catch {
    throw new Error(
      "Unable to reach the server. Check your connection and try again.",
    );
  }

  const parsed = await parseResponseJson<{
    access_token?: string;
    expires_in?: number;
    message?: string;
  }>(response);

  if (!parsed.ok) {
    throw new Error(
      response.ok
        ? "Sign-in did not complete. Please try again."
        : "Sign-in is temporarily unavailable. Please try again.",
    );
  }

  const payload = parsed.data;

  if (response.status === 404) {
    return null;
  }

  if (!response.ok || !payload.access_token) {
    throw new Error(
      payload.message ??
        (response.status === 401
          ? "Invalid email, password, or college code."
          : "Could not sign in. Please try again."),
    );
  }

  return {
    access_token: payload.access_token,
    expires_in: payload.expires_in ?? 3600,
  };
}

async function loginViaApi(input: LoginInput): Promise<{
  access_token: string;
  expires_in: number;
}> {
  const tokens = await apiRequest<TokenPair>("/auth/login", {
    method: "POST",
    body: {
      email: input.email,
      password: input.password,
      tenant_code: input.tenant_code ?? null,
    },
    auth: false,
  });
  setRefreshToken(tokens.refresh_token);
  setSessionIndicatorCookie(tokens.expires_in);
  return {
    access_token: tokens.access_token,
    expires_in: tokens.expires_in,
  };
}

export async function loginWithBff(input: LoginInput): Promise<{
  access_token: string;
  expires_in: number;
}> {
  if (useBffAuth()) {
    const bff = await loginViaBff(input);
    if (bff) {
      return bff;
    }
    /* BFF missing (404) — fall back to direct API. */
  }
  return loginViaApi(input);
}

export async function logoutWithBff(accessToken: string | null): Promise<void> {
  if (useBffAuth()) {
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      credentials: "include",
    });
  }
  clearAccessToken();
  clearRefreshToken();
  clearSessionIndicatorCookie();
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

export async function refreshSessionFromStoredToken(): Promise<string | null> {
  const { getRefreshToken } = await import("@/lib/auth/token-store");
  const refresh = getRefreshToken();
  if (!refresh) return null;
  const tokens = await refreshTokensDirect(refresh);
  setRefreshToken(tokens.refresh_token);
  setSessionIndicatorCookie(tokens.expires_in);
  return tokens.access_token;
}