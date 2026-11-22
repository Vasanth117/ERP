"use client";

import Image from "next/image";

import campusHero from "@/components/icons/erp/loginimage/Unified Campus Management Poster.png";
import { loginBranding } from "@/lib/auth/login-branding";
import type { LoginPortal } from "@/lib/auth/login-portal";

type LoginBrandPanelProps = {
  portal: LoginPortal;
};

export function LoginBrandPanel(_props: LoginBrandPanelProps) {
  const illustrationSrc = loginBranding.illustrationSrc ?? campusHero;

  return (
    <aside className="relative hidden min-h-0 overflow-hidden lg:block lg:min-h-full">
      <Image
        src={illustrationSrc}
        alt={loginBranding.illustrationAlt}
        fill
        className="object-cover object-center"
        sizes="(min-width: 1024px) 480px, 0px"
        priority
      />
    </aside>
  );
}