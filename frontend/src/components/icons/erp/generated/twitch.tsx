import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TwitchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 11V7M16 11V7M21 2H3V18H8V22L12 18H17L21 14V2Z"/>

    </svg>
  );
}
