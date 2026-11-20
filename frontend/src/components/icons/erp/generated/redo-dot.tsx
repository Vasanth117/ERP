import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RedoDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 17C11 17.2652 11.1054 17.5196 11.2929 17.7071C11.4804 17.8946 11.7348 18 12 18C12.2652 18 12.5196 17.8946 12.7071 17.7071C12.8946 17.5196 13 17.2652 13 17C13 16.7348 12.8946 16.4804 12.7071 16.2929C12.5196 16.1054 12.2652 16 12 16C11.7348 16 11.4804 16.1054 11.2929 16.2929C11.1054 16.4804 11 16.7348 11 17Z"/>
      <path d="M21 7V13H15"/>
      <path d="M3 17C3 14.6131 3.94821 12.3239 5.63604 10.636C7.32387 8.94821 9.61305 8 12 8C14.2149 8.00226 16.3511 8.82116 18 10.3L21 13"/>

    </svg>
  );
}
