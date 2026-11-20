import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EggIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 22C18.23 21.95 19.87 16.43 19.5 12C19.14 7.66 15.55 2.04 12 2C8.44997 2.04 4.85997 7.66 4.49997 12C4.12997 16.43 5.76997 21.95 12 22Z"/>

    </svg>
  );
}
