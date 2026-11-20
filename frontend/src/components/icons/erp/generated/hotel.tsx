import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HotelIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 22.0002V15.4302"/>
      <path d="M12 11H12.01"/>
      <path d="M12 7H12.01"/>
      <path d="M14 15.4302V22.0002"/>
      <path d="M15 16C14.1345 15.3509 13.0819 15 12 15C10.9181 15 9.86548 15.3509 9 16"/>
      <path d="M16 11H16.01"/>
      <path d="M16 7H16.01"/>
      <path d="M8 11H8.01"/>
      <path d="M8 7H8.01"/>
      <path d="M6 2H18C18.5304 2 19.0391 2.21071 19.4142 2.58579C19.7893 2.96086 20 3.46957 20 4V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2Z"/>

    </svg>
  );
}
