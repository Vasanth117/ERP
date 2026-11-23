import { AUTH_SESSION_COOKIE } from "@/lib/auth/cookies";

/** Non-httpOnly session marker so middleware matches BFF login (remote API mode). */
export function setSessionIndicatorCookie(maxAgeSeconds: number): void {
  if (typeof document === "undefined") return;
  const secure = window.location.protocol === "https:";
  const parts = [
    `${AUTH_SESSION_COOKIE}=1`,
    "Path=/",
    `Max-Age=${Math.max(60, maxAgeSeconds)}`,
    "SameSite=Lax",
  ];
  if (secure) parts.push("Secure");
  document.cookie = parts.join("; ");
}

export function clearSessionIndicatorCookie(): void {
  if (typeof document === "undefined") return;
  const secure = window.location.protocol === "https:";
  const parts = [
    `${AUTH_SESSION_COOKIE}=`,
    "Path=/",
    "Max-Age=0",
    "SameSite=Lax",
  ];
  if (secure) parts.push("Secure");
  document.cookie = parts.join("; ");
}