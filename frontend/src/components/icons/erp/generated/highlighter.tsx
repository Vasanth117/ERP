import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HighlighterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-6 shrink-0", className)}
      aria-hidden
      {...props}
    >
      <path d="M9 11L3 17V20H12L15 17"/>
      <path d="M22 12L17.4 16.6C17.0262 16.9665 16.5235 17.1717 16 17.1717C15.4765 17.1717 14.9739 16.9665 14.6 16.6L9.40002 11.4C9.03357 11.0261 8.82831 10.5235 8.82831 10C8.82831 9.47649 9.03357 8.97386 9.40002 8.6L14 4"/>

    </svg>
  );
}
