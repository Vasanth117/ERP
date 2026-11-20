import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FlipHorizontal2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 7L8 12L3 17V7Z"/>
      <path d="M21 7L16 12L21 17V7Z"/>
      <path d="M12 20V22"/>
      <path d="M12 14V16"/>
      <path d="M12 8V10"/>
      <path d="M12 2V4"/>

    </svg>
  );
}
