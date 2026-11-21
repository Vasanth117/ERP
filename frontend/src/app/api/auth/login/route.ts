import { NextResponse } from "next/server";

import { normalizeLoginPayload } from "@/lib/auth/login-normalize";
import { apiBaseUrl } from "@/lib/env";
import {
  AUTH_REFRESH_COOKIE,
  AUTH_SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/cookies";
import { type ApiResponse, unwrapApiData } from "@/lib/api/envelope";
import type { TokenPair } from "@/lib/auth/types";

type LoginBody = {
  email?: string;
  password?: string;
  tenant_code?: string;
};

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

export async function POST(request: Request) {
  const body = (await request.json()) as LoginBody;
  const { email, password, tenant_code } = normalizeLoginPayload(body);

  if (!email || !password) {
    return NextResponse.json(
      { message: "Login and password are required" },
      { status: 400 },
    );
  }

  const upstream = await fetch(`${apiBaseUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      tenant_code: tenant_code ?? null,
    }),
  });

  const envelope = (await upstream.json()) as ApiResponse<TokenPair>;

  if (!upstream.ok) {
    let message =
      envelope.error?.message ??
      "Invalid credentials or tenant configuration";
    if (
      upstream.status === 401 &&
      envelope.error?.code === "INVALID_CREDENTIALS"
    ) {
      message = "Invalid email or password.";
    }
    return NextResponse.json(
      {
        message,
        code: envelope.error?.code,
      },
      { status: upstream.status },
    );
  }

  let tokens: TokenPair;
  try {
    tokens = unwrapApiData(envelope);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Login response was invalid";
    return NextResponse.json({ message }, { status: 502 });
  }

  const response = NextResponse.json({
    access_token: tokens.access_token,
    expires_in: tokens.expires_in,
    token_type: tokens.token_type,
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