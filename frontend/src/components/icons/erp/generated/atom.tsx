import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AtomIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 12C11 12.2652 11.1054 12.5196 11.2929 12.7071C11.4804 12.8946 11.7348 13 12 13C12.2652 13 12.5196 12.8946 12.7071 12.7071C12.8946 12.5196 13 12.2652 13 12C13 11.7348 12.8946 11.4804 12.7071 11.2929C12.5196 11.1054 12.2652 11 12 11C11.7348 11 11.4804 11.1054 11.2929 11.2929C11.1054 11.4804 11 11.7348 11 12Z"/>
      <path d="M20.2 20.2C22.24 18.17 20.22 12.84 15.7 8.30001C11.16 3.78001 5.82999 1.76001 3.79999 3.80001C1.75999 5.83001 3.77999 11.16 8.29999 15.7C12.84 20.22 18.17 22.24 20.2 20.2Z"/>
      <path d="M15.7 15.7C20.22 11.16 22.24 5.83001 20.2 3.80001C18.17 1.76001 12.84 3.78001 8.29999 8.30001C3.77999 12.84 1.75999 18.17 3.79999 20.2C5.82999 22.24 11.16 20.22 15.7 15.7Z"/>

    </svg>
  );
}
