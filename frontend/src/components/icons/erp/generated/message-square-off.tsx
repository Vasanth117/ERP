import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MessageSquareOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 15V5C21 4.46957 20.7893 3.96086 20.4142 3.58579C20.0391 3.21071 19.5304 3 19 3H9"/>
      <path d="M2 2L22 22"/>
      <path d="M3.6 3.6001C3.2 3.9001 3 4.4001 3 5.0001V21.0001L7 17.0001H17"/>

    </svg>
  );
}
