import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/env";
import {
  AUTH_REFRESH_COOKIE,
  AUTH_SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/cookies";
import { type ApiResponse, unwrapApiData } from "@/lib/api/envelope";
import type { TokenPair } from "@/lib/auth/types";

function cookieOptions(maxAge: number) {
  const secure = process.env.NODE_ENV === "production";
  return {
    httpOnly: true,
    secure,
    sameSite: "lax" as const,
    path: "/",
    maxAge,
  };
}

export async function POST() {
  const jar = await cookies();
  const refreshToken = jar.get(AUTH_REFRESH_COOKIE)?.value;

  if (!refreshToken) {
    return NextResponse.json({ message: "No refresh session" }, { status: 401 });
  }

  const upstream = await fetch(`${apiBaseUrl()}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const raw = await upstream.text();
  let envelope: ApiResponse<TokenPair>;
  try {
    envelope = JSON.parse(raw) as ApiResponse<TokenPair>;
  } catch {
    return NextResponse.json(
      {
        message:
          raw.trim().slice(0, 120) || "Authentication service unavailable",
      },
      { status: upstream.status >= 400 ? upstream.status : 502 },
    );
  }

  if (!upstream.ok) {
    const response = NextResponse.json(
      {
        message: envelope.error?.message ?? "Session expired",
        code: envelope.error?.code,
      },
      { status: upstream.status },
    );
    response.cookies.delete(AUTH_REFRESH_COOKIE);
    response.cookies.delete(AUTH_SESSION_COOKIE);
    return response;
  }

  const tokens = unwrapApiData(envelope);

  const response = NextResponse.json({
    access_token: tokens.access_token,
    expires_in: tokens.expires_in,
  });

  response.cookies.set(
    AUTH_REFRESH_COOKIE,
    tokens.refresh_token,
    cookieOptions(SESSION_MAX_AGE_SECONDS),
  );
  response.cookies.set(
    AUTH_SESSION_COOKIE,
    "1",
    cookieOptions(tokens.expires_in),
  );

  return response;
}