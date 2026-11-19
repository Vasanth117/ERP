import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/env";
import { AUTH_REFRESH_COOKIE, AUTH_SESSION_COOKIE } from "@/lib/auth/cookies";

export async function POST(request: Request) {
  const jar = await cookies();
  const refreshToken = jar.get(AUTH_REFRESH_COOKIE)?.value ?? null;
  const authorization = request.headers.get("authorization");

  if (authorization) {
    await fetch(`${apiBaseUrl()}/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: authorization,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  const response = new NextResponse(null, { status: 204 });
  response.cookies.delete(AUTH_REFRESH_COOKIE);
  response.cookies.delete(AUTH_SESSION_COOKIE);
  return response;
}