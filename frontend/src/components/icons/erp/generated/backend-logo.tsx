import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

/** Product / backend mark (dashboard tile layout). Source: `backend-logo.svg`. */
export function BackendLogoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="18 16 84 88"
      fill="none"
      role="img"
      className={cn("size-6 shrink-0", className)}
      aria-hidden
      {...props}
    >
      <rect x="18" y="16" width="16" height="88" rx="8" fill="#1B2430" />
      <rect x="18" y="16" width="84" height="16" rx="8" fill="#1B2430" />
      <rect x="18" y="56" width="84" height="16" rx="8" fill="#2F6B4F" />
      <rect x="86" y="56" width="16" height="48" rx="8" fill="#1B2430" />
    </svg>
  );
}