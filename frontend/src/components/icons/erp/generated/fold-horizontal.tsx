import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FoldHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12H8"/>
      <path d="M22 12H16"/>
      <path d="M12 2V4"/>
      <path d="M12 8V10"/>
      <path d="M12 14V16"/>
      <path d="M12 20V22"/>
      <path d="M19 9L16 12L19 15"/>
      <path d="M5 15L8 12L5 9"/>

    </svg>
  );
}
