import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { AUTH_SESSION_COOKIE } from "@/lib/auth/cookies";

/** Public routes — no auth required (Figma main landing at `/`). */
const PUBLIC_PATHS = ["/", "/login", "/under-construction"];

function loginPortalForPath(pathname: string): string | null {
  if (pathname === "/college-admin" || pathname.startsWith("/college-admin/")) {
    return "institution";
  }
  if (pathname === "/student" || pathname.startsWith("/student/")) {
    return "student-performance";
  }
  return null;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api/auth") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  const hasSession = Boolean(request.cookies.get(AUTH_SESSION_COOKIE)?.value);
  const isPublic = PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  );

  if (!hasSession && !isPublic) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    const portal = loginPortalForPath(pathname);
    if (portal) {
      loginUrl.searchParams.set("portal", portal);
    }
    return NextResponse.redirect(loginUrl);
  }

  /* Do not skip /login when a session cookie exists — user may switch accounts. */

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!.*\\..*).*)"],
};