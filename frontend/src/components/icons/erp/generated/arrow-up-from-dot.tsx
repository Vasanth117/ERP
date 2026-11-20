import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowUpFromDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 9L12 2L19 9"/>
      <path d="M12 16V2"/>
      <path d="M11 21C11 21.2652 11.1054 21.5196 11.2929 21.7071C11.4804 21.8946 11.7348 22 12 22C12.2652 22 12.5196 21.8946 12.7071 21.7071C12.8946 21.5196 13 21.2652 13 21C13 20.7348 12.8946 20.4804 12.7071 20.2929C12.5196 20.1054 12.2652 20 12 20C11.7348 20 11.4804 20.1054 11.2929 20.2929C11.1054 20.4804 11 20.7348 11 21Z"/>

    </svg>
  );
}
