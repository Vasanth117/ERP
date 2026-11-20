import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LibraryIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 6L20 20"/>
      <path d="M12 6V20"/>
      <path d="M8 8V20"/>
      <path d="M4 4V20"/>

    </svg>
  );
}
