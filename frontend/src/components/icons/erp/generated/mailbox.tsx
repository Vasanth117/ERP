import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MailboxIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 17C22 17.5304 21.7893 18.0391 21.4142 18.4142C21.0391 18.7893 20.5304 19 20 19H4C3.46957 19 2.96086 18.7893 2.58579 18.4142C2.21071 18.0391 2 17.5304 2 17V9.5C2 7 4 5 6.5 5H18C20.2 5 22 6.8 22 9V17Z"/>
      <path d="M15 9H18V11"/>
      <path d="M6.5 5C9 5 11 7 11 9.5V17C11 17.5304 10.7893 18.0391 10.4142 18.4142C10.0391 18.7893 9.53043 19 9 19"/>
      <path d="M6 10H7"/>

    </svg>
  );
}
