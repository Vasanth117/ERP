"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getDevStudentLoginDefaults } from "@/lib/auth/dev-login-defaults";
import { getAccessToken } from "@/lib/auth/token-store";

export function StudentAuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(getAccessToken()));
    setReady(true);
  }, []);

  const me = useCurrentUser(hasToken);

  if (!ready) {
    return null;
  }

  const returnUrl = encodeURIComponent(pathname ?? "/student/dashboard");
  const studentLoginHref = `/login?portal=student-performance&next=${returnUrl}`;

  if (!hasToken) {
    return (
      <StudentGatePanel
        title="Sign in to Student Portal"
        description={
          <>
            Student pages call <code className="text-[#245dd8]">/api/v1/students/me/*</code> with a{" "}
            <strong className="font-medium text-[#374151]">student-role</strong> session — not the
            College Admin demo account.
          </>
        }
        loginHref={studentLoginHref}
        loginLabel="Student sign in"
        devHint
      />
    );
  }

  if (me.isLoading) {
    return <StudentSessionLoading />;
  }

  if (me.isError || !me.data) {
    return (
      <StudentGatePanel
        title="Sign in required"
        description="Your session is missing or expired. Sign in with the student demo account to load live data."
        loginHref={studentLoginHref}
        loginLabel="Student sign in"
        devHint
      />
    );
  }

  if (me.data.role !== "student") {
    return (
      <StudentGatePanel
        title="Student account required"
        description={
          <>
            You are signed in as <strong className="font-medium text-[#374151]">{me.data.role}</strong> (
            {me.data.email || me.data.full_name}). Open the student login page and use{" "}
            <strong className="font-medium text-[#374151]">Student ID</strong> credentials (e.g. seeded{" "}
            <code className="text-[#245dd8]">{getDevStudentLoginDefaults().identifier || "STU-DEMO001"}</code>
            ).
          </>
        }
        loginHref={studentLoginHref}
        loginLabel="Switch to student login"
        secondaryHref="/college-admin/dashboard"
        secondaryLabel="Back to College Admin"
      />
    );
  }

  return children;
}

function StudentSessionLoading() {
  return (
    <div className="mx-auto max-w-lg rounded-xl border border-[#dce3ec] bg-white p-8 text-center text-sm text-[#607086]">
      Checking session…
    </div>
  );
}

function StudentGatePanel({
  title,
  description,
  loginHref,
  loginLabel,
  devHint,
  secondaryHref,
  secondaryLabel,
}: {
  title: string;
  description: ReactNode;
  loginHref: string;
  loginLabel: string;
  devHint?: boolean;
  secondaryHref?: string;
  secondaryLabel?: string;
}) {
  const dev = getDevStudentLoginDefaults();

  return (
    <div className="mx-auto max-w-lg rounded-xl border border-[#e8ecf2] bg-white p-8 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-[#111827]">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-[#6b7280]">{description}</p>
      {devHint && dev.identifier && process.env.NODE_ENV === "development" ? (
        <p className="mt-3 text-xs text-[#9ca3af]">
          Local seed: ID {dev.identifier} · run{" "}
          <code className="text-[#245dd8]">bootstrap_dev_portal_users.py</code>
        </p>
      ) : null}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        <Link
          href={loginHref}
          className="inline-flex h-10 items-center rounded-lg bg-[#245dd8] px-5 text-sm font-medium text-white hover:bg-[#1f4fb8]"
        >
          {loginLabel}
        </Link>
        {secondaryHref && secondaryLabel ? (
          <Link
            href={secondaryHref}
            className="inline-flex h-10 items-center rounded-lg border border-[#e5e7eb] bg-white px-5 text-sm font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            {secondaryLabel}
          </Link>
        ) : null}
      </div>
    </div>
  );
}