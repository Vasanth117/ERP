import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TowerControlIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.2 12.27L20 6H4L5.8 12.27C5.85829 12.4779 5.98233 12.6614 6.15358 12.793C6.32482 12.9246 6.53406 12.9972 6.75 13H17.25C17.4677 12.9994 17.6792 12.9278 17.8524 12.796C18.0257 12.6643 18.1512 12.4796 18.21 12.27H18.2Z"/>
      <path d="M8 13V22"/>
      <path d="M16 22V13"/>
      <path d="M9 6L10 13"/>
      <path d="M15 6L14 13"/>
      <path d="M12 6V2"/>
      <path d="M13 2H11"/>

    </svg>
  );
}
