import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MonitorOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 17H4C3.46957 17 2.96086 16.7893 2.58579 16.4142C2.21071 16.0391 2 15.5304 2 15V5C2 3.5 3 3 3 3"/>
      <path d="M22 15V5C22 4.46957 21.7893 3.96086 21.4142 3.58579C21.0391 3.21071 20.5304 3 20 3H9"/>
      <path d="M8 21H16"/>
      <path d="M12 17V21"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
