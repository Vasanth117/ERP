import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CaseUpperIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 15L7 7L11 15"/>
      <path d="M4 13H10"/>
      <path d="M15 11H19.5C20.0304 11 20.5391 11.2107 20.9142 11.5858C21.2893 11.9609 21.5 12.4696 21.5 13C21.5 13.5304 21.2893 14.0391 20.9142 14.4142C20.5391 14.7893 20.0304 15 19.5 15H15V7H19C19.5304 7 20.0391 7.21071 20.4142 7.58579C20.7893 7.96086 21 8.46957 21 9C21 9.53043 20.7893 10.0391 20.4142 10.4142C20.0391 10.7893 19.5304 11 19 11"/>

    </svg>
  );
}
