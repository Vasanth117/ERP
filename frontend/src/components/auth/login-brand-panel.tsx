"use client";

import Image from "next/image";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  loginBranding,
  loginLeftPanelCopy,
} from "@/lib/auth/login-branding";
import type { LoginPortal } from "@/lib/auth/login-portal";
import { portalTitle } from "@/lib/auth/login-portal";

type LoginBrandPanelProps = {
  portal: LoginPortal;
};

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

export function LoginBrandPanel({ portal }: LoginBrandPanelProps) {
  const { colors } = loginBranding;
  const copy = loginLeftPanelCopy(portal);
  const illustrationSrc =
    loginBranding.illustrationSrc ?? loginBranding.defaultIllustrationSrc;

  return (
    <aside
      className="relative hidden min-h-0 overflow-hidden lg:flex lg:flex-col"
      style={{
        background: `linear-gradient(165deg, ${colors.panelGradientFrom} 0%, ${colors.panelGradientVia} 42%, ${colors.panelGradientTo} 100%)`,
      }}
    >
      <div className="pointer-events-none absolute -left-10 top-8 size-40 rounded-full bg-[#245dd8]/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 size-48 rounded-full bg-[#4c86f5]/15 blur-3xl" />

      <div className="relative z-10 flex flex-1 flex-col p-9">
        <div className="flex items-center gap-2.5">
          <div
            className="flex size-10 items-center justify-center rounded-xl border shadow-sm"
            style={{
              backgroundColor: colors.logoBackground,
              borderColor: colors.logoBorder,
            }}
          >
            <CollegeAdminIcon
              name={portalIcon(portal)}
              size={22}
              className="text-[#245dd8]"
            />
          </div>
          <span
            className="text-[17px] font-semibold tracking-tight"
            style={{ color: colors.headline }}
          >
            {loginBranding.productName}
          </span>
        </div>

        <div className="mt-8 max-w-[320px]">
          <p
            className="text-[13px] font-medium uppercase tracking-wide"
            style={{ color: colors.tagline }}
          >
            {portalTitle(portal)}
          </p>
          <h2
            className="mt-2 text-[26px] font-bold leading-tight"
            style={{ color: colors.headline }}
          >
            {copy.headline}
          </h2>
          <p
            className="mt-3 text-[15px] leading-relaxed"
            style={{ color: colors.tagline }}
          >
            {copy.tagline}
          </p>
        </div>

        <div className="relative mt-auto flex flex-1 items-end justify-center pt-4">
          <div className="relative h-[180px] w-full max-w-[300px]">
            <Image
              src={illustrationSrc}
              alt={loginBranding.illustrationAlt}
              fill
              className="object-contain object-bottom"
              sizes="(min-width: 1024px) 340px, 0px"
              priority
            />
          </div>
        </div>
      </div>
    </aside>
  );
}