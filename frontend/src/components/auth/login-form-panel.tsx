import Link from "next/link";
import type { ReactNode } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  loginBranding,
  loginFormSubtitle,
  loginFormTitle,
} from "@/lib/auth/login-branding";
import type { LoginPortal } from "@/lib/auth/login-portal";
import { portalTitle } from "@/lib/auth/login-portal";

function portalIcon(portal: LoginPortal) {
  switch (portal) {
    case "institution":
      return "building-2" as const;
    case "student-performance":
      return "graduation-cap" as const;
    default:
      return "layout-grid" as const;
  }
}

type LoginFormPanelProps = {
  portal: LoginPortal;
  children: ReactNode;
};

export function LoginFormPanel({ portal, children }: LoginFormPanelProps) {
  const { colors } = loginBranding;

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden bg-white font-sans antialiased">
      <div className="flex min-h-0 flex-1 flex-col justify-center overflow-hidden px-8 py-6 sm:px-10 lg:px-10 lg:py-7">
        <div className="mb-5 flex items-center gap-2.5 lg:hidden">
          <div
            className="flex size-9 items-center justify-center rounded-lg border shadow-sm"
            style={{
              borderColor: colors.logoBorder,
              backgroundColor: colors.logoBackground,
            }}
          >
            <CollegeAdminIcon
              name={portalIcon(portal)}
              size={20}
              className="text-[#245dd8]"
            />
          </div>
          <div>
            <p
              className="text-[15px] font-semibold tracking-tight"
              style={{ color: colors.headline }}
            >
              {loginBranding.productName}
            </p>
            <p className="text-[12px] text-[#64748b]">{portalTitle(portal)}</p>
          </div>
        </div>

        <header className="mb-4 w-full shrink-0 border-b border-[#eef2f7] pb-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#245dd8]">
            {portalTitle(portal)}
          </p>
          <h1 className="mt-2 text-[22px] font-bold leading-tight tracking-[-0.02em] text-[#0f2744] xl:text-[24px]">
            {loginFormTitle(portal)}
          </h1>
          <p className="mt-2 max-w-[22rem] text-[13px] leading-relaxed text-[#5c6b7e]">
            {loginFormSubtitle(portal)}
          </p>
        </header>

        <div className="w-full">{children}</div>

        <p className="mt-4 shrink-0 text-[13px] text-[#64748b]">
          <Link
            href="/"
            className="font-semibold text-[#245dd8] transition-colors hover:text-[#1e52c4] hover:underline"
          >
            ← Back to modules
          </Link>
        </p>
      </div>
    </section>
  );
}