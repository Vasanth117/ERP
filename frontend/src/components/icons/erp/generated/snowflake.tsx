import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SnowflakeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12H22"/>
      <path d="M12 2V22"/>
      <path d="M20 16L16 12L20 8"/>
      <path d="M4 8L8 12L4 16"/>
      <path d="M16 4L12 8L8 4"/>
      <path d="M8 20L12 16L16 20"/>

    </svg>
  );
}
