import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PhilippinePesoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20 11H4"/>
      <path d="M20 7H4"/>
      <path d="M7 21V4C7 3.73478 7.10536 3.48043 7.29289 3.29289C7.48043 3.10536 7.73478 3 8 3H12C13.5913 3 15.1174 3.63214 16.2426 4.75736C17.3679 5.88258 18 7.4087 18 9C18 10.5913 17.3679 12.1174 16.2426 13.2426C15.1174 14.3679 13.5913 15 12 15H7"/>

    </svg>
  );
}
