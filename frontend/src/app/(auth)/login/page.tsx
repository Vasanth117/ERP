import { Suspense } from "react";

import { LoginFormLoader } from "@/components/auth/login-form-loader";

export default function LoginPage() {
  return (
    <div className="h-full min-h-0">
      <Suspense
        fallback={<div className="text-sm text-muted-foreground">Loading…</div>}
      >
        <LoginFormLoader />
      </Suspense>
    </div>
  );
}