import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowDown01Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 16L7 20L11 16"/>
      <path d="M7 20V4"/>
      <path d="M17 4C17.5304 4 18.0391 4.21071 18.4142 4.58579C18.7893 4.96086 19 5.46957 19 6V8C19 8.53043 18.7893 9.03914 18.4142 9.41421C18.0391 9.78929 17.5304 10 17 10C16.4696 10 15.9609 9.78929 15.5858 9.41421C15.2107 9.03914 15 8.53043 15 8V6C15 5.46957 15.2107 4.96086 15.5858 4.58579C15.9609 4.21071 16.4696 4 17 4Z"/>
      <path d="M17 20V14H15"/>
      <path d="M15 20H19"/>

    </svg>
  );
}
