import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReplyAllIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 17L2 12L7 7"/>
      <path d="M12 17L7 12L12 7"/>
      <path d="M22 18V16C22 14.9391 21.5786 13.9217 20.8284 13.1716C20.0783 12.4214 19.0609 12 18 12H7"/>

    </svg>
  );
}
