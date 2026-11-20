import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MicrochipIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 12H20"/>
      <path d="M18 16H20"/>
      <path d="M18 20H20"/>
      <path d="M18 4H20"/>
      <path d="M18 8H20"/>
      <path d="M4 12H6"/>
      <path d="M4 16H6"/>
      <path d="M4 20H6"/>
      <path d="M4 4H6"/>
      <path d="M4 8H6"/>
      <path d="M8 2C7.46957 2 6.96086 2.21071 6.58579 2.58579C6.21071 2.96086 6 3.46957 6 4V20C6 20.5304 6.21071 21.0391 6.58579 21.4142C6.96086 21.7893 7.46957 22 8 22H16C16.5304 22 17.0391 21.7893 17.4142 21.4142C17.7893 21.0391 18 20.5304 18 20V4C18 3.46957 17.7893 2.96086 17.4142 2.58579C17.0391 2.21071 16.5304 2 16 2H14.5C14.224 2 14.006 2.227 13.938 2.495C13.8282 2.92565 13.5781 3.30747 13.2271 3.58016C12.8762 3.85285 12.4444 4.00088 12 4.00088C11.5556 4.00088 11.1238 3.85285 10.7729 3.58016C10.4219 3.30747 10.1718 2.92565 10.062 2.495C9.994 2.227 9.776 2 9.5 2H8Z"/>

    </svg>
  );
}
