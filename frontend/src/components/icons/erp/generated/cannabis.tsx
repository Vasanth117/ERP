import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CannabisIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 22V18"/>
      <path d="M7 12C5.5 12 2.5 13.5 2 15C5.5 16.5 8 16 8 16C6.5 17.5 6 19.5 6 21C8.5 21 10.5 19.5 12 18C13.5 19.5 15.5 21 18 21C18 19.5 17.5 17.5 16 16C16 16 18.5 16.5 22 15C21.5 13.5 18.5 12 17 12C18.5 11 21 8 21 6C18.5 6 15.5 7.5 14 9C14 6.5 13.5 4 12 2C10.5 4 10 6.5 10 9C8.5 7.5 5.5 6 3 6C3 8 5.5 11 7 12Z"/>

    </svg>
  );
}
