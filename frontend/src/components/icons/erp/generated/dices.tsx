import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DicesIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 10H12C12.5304 10 13.0391 10.2107 13.4142 10.5858C13.7893 10.9609 14 11.4696 14 12V20C14 20.5304 13.7893 21.0391 13.4142 21.4142C13.0391 21.7893 12.5304 22 12 22H4C3.46957 22 2.96086 21.7893 2.58579 21.4142C2.21071 21.0391 2 20.5304 2 20V12C2 11.4696 2.21071 10.9609 2.58579 10.5858C2.96086 10.2107 3.46957 10 4 10Z"/>
      <path d="M17.92 14.0003L21.42 10.5003C21.791 10.0888 21.9964 9.55437 21.9964 9.0003C21.9964 8.44622 21.791 7.9118 21.42 7.5003L16.42 2.5803C16.0085 2.20926 15.4741 2.00391 14.92 2.00391C14.3659 2.00391 13.8315 2.20926 13.42 2.5803L10 6.0003"/>
      <path d="M6 18H6.01"/>
      <path d="M10 14H10.01"/>
      <path d="M15 6H15.01"/>
      <path d="M18 9H18.01"/>

    </svg>
  );
}
