import type { ReactNode } from "react";

import { LoginBrandPanel } from "@/components/auth/login-brand-panel";
import { LoginFormPanel } from "@/components/auth/login-form-panel";
import { loginBranding } from "@/lib/auth/login-branding";
import type { LoginPortal } from "@/lib/auth/login-portal";

type LoginPageChromeProps = {
  portal: LoginPortal;
  children: ReactNode;
};

export function LoginPageChrome({ portal, children }: LoginPageChromeProps) {
  const { colors } = loginBranding;

  return (
    <div
      className="flex h-full min-h-0 items-center justify-center overflow-hidden px-4 py-4 font-sans sm:px-6"
      style={{ backgroundColor: colors.pageBackground }}
    >
      <article
        className="grid w-full max-w-[960px] overflow-hidden rounded-2xl border bg-white shadow-[0_8px_40px_rgba(23,43,69,0.08)] max-lg:h-auto lg:h-[min(560px,calc(100dvh-2rem))] lg:max-h-[560px] lg:grid-cols-2 lg:min-h-0"
        style={{ borderColor: colors.cardBorder }}
      >
        <LoginBrandPanel portal={portal} />
        <LoginFormPanel portal={portal}>{children}</LoginFormPanel>
      </article>
    </div>
  );
}