import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TicketsPlaneIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10.5 17H11.727C12.2244 16.9999 12.7039 16.8146 13.072 16.48L18 12"/>
      <path d="M12 13.5L15.75 14"/>
      <path d="M4.5 7.99979L15.08 2.93979C15.1999 2.88239 15.3301 2.84948 15.4629 2.84299C15.5957 2.8365 15.7285 2.85656 15.8535 2.902C15.9784 2.94744 16.0931 3.01735 16.1907 3.10763C16.2883 3.19791 16.367 3.30675 16.422 3.42779L18.5 7.99979"/>
      <path d="M6 10V8"/>
      <path d="M6 14V15"/>
      <path d="M6 19V21"/>
      <path d="M4 8H20C20.5304 8 21.0391 8.21071 21.4142 8.58579C21.7893 8.96086 22 9.46957 22 10V19C22 19.5304 21.7893 20.0391 21.4142 20.4142C21.0391 20.7893 20.5304 21 20 21H4C3.46957 21 2.96086 20.7893 2.58579 20.4142C2.21071 20.0391 2 19.5304 2 19V10C2 9.46957 2.21071 8.96086 2.58579 8.58579C2.96086 8.21071 3.46957 8 4 8Z"/>

    </svg>
  );
}
