"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { homePathForRole } from "@/lib/auth/role-home";

/** Temporary router — sends each role to its module home (not a product dashboard). */
export default function DashboardPage() {
  const router = useRouter();
  const { data: user, isLoading, error } = useCurrentUser();

  useEffect(() => {
    if (!user) {
      return;
    }
    const target = homePathForRole(user.role);
    if (target !== "/dashboard") {
      router.replace(target);
    }
  }, [user, router]);

  if (isLoading) {
    return (
      <p className="text-sm text-muted-foreground">Loading your workspace…</p>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-destructive">
        Session expired — please{" "}
        <a href="/login" className="underline">
          sign in again
        </a>
        .
      </p>
    );
  }

  if (user) {
    return (
      <p className="text-sm text-muted-foreground">Opening your portal…</p>
    );
  }

  return null;
}