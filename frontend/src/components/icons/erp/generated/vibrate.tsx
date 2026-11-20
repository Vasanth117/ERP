import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function VibrateIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 8L4 10L2 12L4 14L2 16"/>
      <path d="M22 8L20 10L22 12L20 14L22 16"/>
      <path d="M9 5H15C15.2652 5 15.5196 5.10536 15.7071 5.29289C15.8946 5.48043 16 5.73478 16 6V18C16 18.2652 15.8946 18.5196 15.7071 18.7071C15.5196 18.8946 15.2652 19 15 19H9C8.73478 19 8.48043 18.8946 8.29289 18.7071C8.10536 18.5196 8 18.2652 8 18V6C8 5.73478 8.10536 5.48043 8.29289 5.29289C8.48043 5.10536 8.73478 5 9 5Z"/>

    </svg>
  );
}
