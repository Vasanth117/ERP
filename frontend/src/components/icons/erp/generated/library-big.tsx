import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LibraryBigIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 3H10C10.2652 3 10.5196 3.10536 10.7071 3.29289C10.8946 3.48043 11 3.73478 11 4V20C11 20.2652 10.8946 20.5196 10.7071 20.7071C10.5196 20.8946 10.2652 21 10 21H4C3.73478 21 3.48043 20.8946 3.29289 20.7071C3.10536 20.5196 3 20.2652 3 20V4C3 3.73478 3.10536 3.48043 3.29289 3.29289C3.48043 3.10536 3.73478 3 4 3Z"/>
      <path d="M7 3V21"/>
      <path d="M20.4 18.9C20.6 19.4 20.3 20 19.8 20.2L17.9 20.9C17.4 21.1 16.8 20.8 16.6 20.3L11.1 5.1C10.9 4.6 11.2 4 11.7 3.8L13.6 3.1C14.1 2.9 14.7 3.2 14.9 3.7L20.4 18.9Z"/>

    </svg>
  );
}
