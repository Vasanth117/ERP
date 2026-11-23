import { apiRequest } from "@/lib/api/client";
import { parseResponseJson } from "@/lib/api/parse-response-body";
import type { AuthUser, LoginInput, TokenPair } from "@/lib/auth/types";

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

export async function loginWithBff(input: LoginInput): Promise<{
  access_token: string;
  expires_in: number;
}> {
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