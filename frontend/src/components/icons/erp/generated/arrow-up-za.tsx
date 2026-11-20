import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowUpZaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 8L7 4L11 8"/>
      <path d="M7 4V20"/>
      <path d="M15 4H20L15 10H20"/>
      <path d="M15 20V16.5C15 15.837 15.2634 15.2011 15.7322 14.7322C16.2011 14.2634 16.837 14 17.5 14C18.163 14 18.7989 14.2634 19.2678 14.7322C19.7366 15.2011 20 15.837 20 16.5V20"/>
      <path d="M20 18H15"/>

    </svg>
  );
}
