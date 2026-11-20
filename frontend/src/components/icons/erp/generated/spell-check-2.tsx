import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SpellCheck2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 16L12 4L18 16"/>
      <path d="M8 12H16"/>
      <path d="M4 21C5.1 21 5.1 20 6.3 20C7.5 20 7.4 21 8.6 21C9.7 21 9.7 20 10.9 20C12 20 12 21 13.2 21C14.3 21 14.3 20 15.5 20C16.6 20 16.6 21 17.8 21C18.9 21 18.9 20 20.1 20"/>

    </svg>
  );
}
