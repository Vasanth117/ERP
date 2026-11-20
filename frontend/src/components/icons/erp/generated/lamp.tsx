import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2H16L20 12H4L8 2Z"/>
      <path d="M12 12V18"/>
      <path d="M8 22V20C8 18.9 8.9 18 10 18H14C14.5304 18 15.0391 18.2107 15.4142 18.5858C15.7893 18.9609 16 19.4696 16 20V22H8Z"/>

    </svg>
  );
}
