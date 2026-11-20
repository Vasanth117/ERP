import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function JapaneseYenIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 9.5V21M12 9.5L6 3M12 9.5L18 3"/>
      <path d="M6 15H18"/>
      <path d="M6 11H18"/>

    </svg>
  );
}
