"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

export default function DashboardPage() {
  const { data: user, isLoading, error } = useCurrentUser();

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Foundation shell — module portals (student, faculty, admin) will plug
          in here.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
          <CardDescription>
            Loaded from <code className="text-xs">GET /api/v1/auth/me</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm">
          {isLoading ? (
            <p className="text-muted-foreground">Loading user…</p>
          ) : error ? (
            <p className="text-destructive">
              {error instanceof Error
                ? error.message
                : "Could not load profile"}
            </p>
          ) : user ? (
            <dl className="grid gap-2 sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Name</dt>
                <dd className="font-medium">{user.full_name}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Email</dt>
                <dd className="font-medium">{user.email}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Role</dt>
                <dd className="font-medium">{user.role}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Tenant</dt>
                <dd className="font-medium">{user.tenant_id ?? "Platform"}</dd>
              </div>
            </dl>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}