"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { getAccessToken } from "@/lib/auth/token-store";

export function CollegeAdminAuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(getAccessToken()));
    setReady(true);
  }, []);

  if (!ready) {
    return null;
  }

  if (!hasToken) {
    const returnUrl = encodeURIComponent(pathname ?? "/college-admin/dashboard");
    return (
      <div className="mx-auto max-w-lg rounded-xl border border-[#e8ecf2] bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-[#111827]">Sign in to College Admin</h2>
        <p className="mt-2 text-sm text-[#6b7280]">
          API pages need an active session. Use the demo tenant after running{" "}
          <code className="text-[#245dd8]">bootstrap_dev_college_admin.py</code>.
        </p>
        <p className="mt-2 text-xs text-[#9ca3af]">
          Dev: admin@demo-college.edu · demo-college — or admin@ghit-demo.edu · ghit-demo after{" "}
          <code className="text-[#245dd8]">seed_demo_college.py --profile enterprise</code>. Enable
          Demo mode in the sidebar to browse showcase data.
        </p>
        <Link
          href={`/login?portal=institution&next=${returnUrl}`}
          className="mt-6 inline-flex h-10 items-center rounded-lg bg-[#245dd8] px-5 text-sm font-medium text-white hover:bg-[#1f4fb8]"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return children;
}