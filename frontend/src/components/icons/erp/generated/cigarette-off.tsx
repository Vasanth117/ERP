import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CigaretteOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 12H3C2.73478 12 2.48043 12.1054 2.29289 12.2929C2.10536 12.4804 2 12.7348 2 13V15C2 15.2652 2.10536 15.5196 2.29289 15.7071C2.48043 15.8946 2.73478 16 3 16H16"/>
      <path d="M18 8C18 5.5 16 5.5 16 3"/>
      <path d="M2 2L22 22"/>
      <path d="M21 12C21.2652 12 21.5196 12.1054 21.7071 12.2929C21.8946 12.4804 22 12.7348 22 13V15C22 15.1755 21.9538 15.348 21.866 15.5C21.7783 15.652 21.652 15.7782 21.5 15.866"/>
      <path d="M22 8C22 5.5 20 5.5 20 3"/>
      <path d="M7 12V16"/>

    </svg>
  );
}
