import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EggFriedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 12.5C8 13.4283 8.36875 14.3185 9.02513 14.9749C9.6815 15.6313 10.5717 16 11.5 16C12.4283 16 13.3185 15.6313 13.9749 14.9749C14.6313 14.3185 15 13.4283 15 12.5C15 11.5717 14.6313 10.6815 13.9749 10.0251C13.3185 9.36875 12.4283 9 11.5 9C10.5717 9 9.6815 9.36875 9.02513 10.0251C8.36875 10.6815 8 11.5717 8 12.5Z"/>
      <path d="M3 8C3 4.5 5.5 2 9.5 2C14.5 2 14.33 5 17 7C19.67 9 22 9 22 13C22 17.5 19.5 19.5 15 19.5C12.5 19.5 12.5 22 9 22C5.5 22 2 20 2 16.5C2 13.5 3.5 13.5 3.5 11.5C3.5 10 3 9 3 8Z"/>

    </svg>
  );
}
