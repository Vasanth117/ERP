"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { logoutWithBff } from "@/features/auth/api";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import {
  clearAccessToken,
  getAccessToken,
} from "@/lib/auth/token-store";

export function AppHeader() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  async function handleLogout() {
    try {
      await logoutWithBff(getAccessToken());
    } catch {
      // Still clear local session if upstream fails.
    }
    clearAccessToken();
    toast.message("Signed out");
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4 md:px-6">
      <div className="flex flex-col">
        <span className="text-sm font-medium text-foreground">College ERP</span>
        <span className="text-xs text-muted-foreground">
          {isLoading
            ? "Loading profile…"
            : user
              ? `${user.full_name} · ${user.role}`
              : "Not signed in"}
        </span>
      </div>
      <Button variant="outline" size="sm" onClick={handleLogout}>
        <LogOut className="size-4" />
        Sign out
      </Button>
    </header>
  );
}