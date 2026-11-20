import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CalendarClockIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 7.5V6C21 5.46957 20.7893 4.96086 20.4142 4.58579C20.0391 4.21071 19.5304 4 19 4H5C4.46957 4 3.96086 4.21071 3.58579 4.58579C3.21071 4.96086 3 5.46957 3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H8.5"/>
      <path d="M16 2V6"/>
      <path d="M8 2V6"/>
      <path d="M3 10H8"/>
      <path d="M17.5 17.5L16 16.3V14"/>
      <path d="M10 16C10 17.5913 10.6321 19.1174 11.7574 20.2426C12.8826 21.3679 14.4087 22 16 22C17.5913 22 19.1174 21.3679 20.2426 20.2426C21.3679 19.1174 22 17.5913 22 16C22 14.4087 21.3679 12.8826 20.2426 11.7574C19.1174 10.6321 17.5913 10 16 10C14.4087 10 12.8826 10.6321 11.7574 11.7574C10.6321 12.8826 10 14.4087 10 16Z"/>

    </svg>
  );
}
