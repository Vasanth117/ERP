import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CodepenIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2L22 8.5V15.5L12 22L2 15.5V8.5L12 2Z"/>
      <path d="M12 22V15.5"/>
      <path d="M22 8.5L12 15.5L2 8.5"/>
      <path d="M2 15.5L12 8.5L22 15.5"/>
      <path d="M12 2V8.5"/>

    </svg>
  );
}
