import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowBigLeftDashIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19 15V9"/>
      <path d="M15 15H12V19L5 12L12 5V9H15V15Z"/>

    </svg>
  );
}
