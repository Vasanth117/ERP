import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FramerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 16V23L5 16V9H12M5 16H12M12 9H19V2H5L12 9ZM12 9L19 16H12"/>

    </svg>
  );
}
