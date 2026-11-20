"use client";

import { useEffect } from "react";

import { notifySessionRestored } from "@/lib/auth/session-ready";
import { getAccessToken, setAccessToken } from "@/lib/auth/token-store";

/**
 * After a full page reload the httpOnly session cookie may still be valid while
 * the in-memory / sessionStorage access token is empty — refresh via BFF.
 */
export function AuthSessionBootstrap() {
  useEffect(() => {
    if (getAccessToken()) {
      return;
    }
    void (async () => {
      try {
        const res = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) {
          return;
        }
        const body = (await res.json()) as { access_token?: string };
        if (body.access_token) {
          setAccessToken(body.access_token);
          notifySessionRestored();
        }
      } catch {
        /* ignore — user will be sent to login by gates/middleware */
      } finally {
        notifySessionRestored();
      }
    })();
  }, []);

  return null;
}