import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MergeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 6L12 2L16 6"/>
      <path d="M12 2V12.3C12.0057 12.8326 11.905 13.361 11.7037 13.8542C11.5025 14.3474 11.2047 14.7954 10.828 15.172L4 22"/>
      <path d="M20 22L15 17"/>

    </svg>
  );
}
