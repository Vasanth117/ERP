import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SignpostBigIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 9H4L2 7L4 5H10"/>
      <path d="M14 5H20L22 7L20 9H14"/>
      <path d="M10 22V4C10 3.46957 10.2107 2.96086 10.5858 2.58579C10.9609 2.21071 11.4696 2 12 2C12.5304 2 13.0391 2.21071 13.4142 2.58579C13.7893 2.96086 14 3.46957 14 4V22"/>
      <path d="M8 22H16"/>

    </svg>
  );
}
