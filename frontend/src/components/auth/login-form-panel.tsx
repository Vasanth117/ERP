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
  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden bg-white">
      <div className="flex min-h-0 flex-1 flex-col justify-center overflow-hidden px-8 py-7 sm:px-10 lg:px-11">
        <div className="mb-4 flex items-center gap-2.5 lg:hidden">
          <div className="flex size-9 items-center justify-center rounded-lg border border-[#dbeafe] bg-[#f8fafc]">
            <CollegeAdminIcon
              name={portalIcon(portal)}
              size={20}
              className="text-[#245dd8]"
            />
          </div>
          <div>
            <p className="text-[15px] font-semibold text-[#172b45]">
              {loginBranding.productName}
            </p>
            <p className="text-[12px] text-[#64748b]">{portalTitle(portal)}</p>
          </div>
        </div>

        <header className="mb-5">
          <h1 className="text-[21px] font-bold tracking-tight text-[#172b45] sm:text-[23px]">
            {loginFormTitle(portal)}
          </h1>
          <p className="mt-1.5 text-[14px] leading-snug text-[#64748b]">
            {loginFormSubtitle(portal)}
          </p>
        </header>

        <div className="w-full max-w-[400px]">{children}</div>

        <p className="mt-5 shrink-0 text-[14px] text-[#64748b]">
          <Link
            href="/"
            className="font-medium hover:underline"
            style={{ color: loginBranding.colors.primary }}
          >
            Back to modules
          </Link>
        </p>
      </div>
    </section>
  );
}