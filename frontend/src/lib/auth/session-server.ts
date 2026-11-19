import { cookies } from "next/headers";

import {
  AUTH_REFRESH_COOKIE,
  AUTH_SESSION_COOKIE,
} from "@/lib/auth/cookies";

export async function hasServerSession(): Promise<boolean> {
  const jar = await cookies();
  return Boolean(jar.get(AUTH_SESSION_COOKIE)?.value);
}

export async function getServerRefreshToken(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get(AUTH_REFRESH_COOKIE)?.value;
}