import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11.1 12.0996C11.1 12.3648 11.2054 12.6192 11.3929 12.8067C11.5804 12.9943 11.8348 13.0996 12.1 13.0996C12.3652 13.0996 12.6196 12.9943 12.8071 12.8067C12.9946 12.6192 13.1 12.3648 13.1 12.0996C13.1 11.8344 12.9946 11.58 12.8071 11.3925C12.6196 11.205 12.3652 11.0996 12.1 11.0996C11.8348 11.0996 11.5804 11.205 11.3929 11.3925C11.2054 11.58 11.1 11.8344 11.1 12.0996Z"/>

    </svg>
  );
}
