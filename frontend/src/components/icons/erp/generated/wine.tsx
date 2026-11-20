import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WineIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 22H16"/>
      <path d="M7 10H17"/>
      <path d="M12 15V22"/>
      <path d="M12 15C13.3261 15 14.5979 14.4732 15.5355 13.5355C16.4732 12.5979 17 11.3261 17 10C17 8 16.5 6 15 2H9C7.5 6 7 8 7 10C7 11.3261 7.52678 12.5979 8.46447 13.5355C9.40215 14.4732 10.6739 15 12 15Z"/>

    </svg>
  );
}
