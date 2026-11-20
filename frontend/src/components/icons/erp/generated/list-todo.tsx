import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListTodoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 5H8C8.26522 5 8.51957 5.10536 8.70711 5.29289C8.89464 5.48043 9 5.73478 9 6V10C9 10.2652 8.89464 10.5196 8.70711 10.7071C8.51957 10.8946 8.26522 11 8 11H4C3.73478 11 3.48043 10.8946 3.29289 10.7071C3.10536 10.5196 3 10.2652 3 10V6C3 5.73478 3.10536 5.48043 3.29289 5.29289C3.48043 5.10536 3.73478 5 4 5Z"/>
      <path d="M3 17L5 19L9 15"/>
      <path d="M13 6H21"/>
      <path d="M13 12H21"/>
      <path d="M13 18H21"/>

    </svg>
  );
}
