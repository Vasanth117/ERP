import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CalendarHeartIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 10H21V6C21 5.46957 20.7893 4.96086 20.4142 4.58579C20.0391 4.21071 19.5304 4 19 4H5C4.46957 4 3.96086 4.21071 3.58579 4.58579C3.21071 4.96086 3 5.46957 3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H12"/>
      <path d="M8 2V6"/>
      <path d="M16 2V6"/>
      <path d="M21.29 14.7002C20.9493 14.3611 20.5156 14.1307 20.0439 14.0382C19.5722 13.9456 19.0836 13.995 18.64 14.1802C18.34 14.3002 18.07 14.4802 17.84 14.7102L17.5 15.0502L17.15 14.7102C16.8104 14.3694 16.3772 14.1372 15.9055 14.0428C15.4337 13.9485 14.9446 13.9963 14.5 14.1802C14.2 14.3002 13.94 14.4802 13.71 14.7102C12.76 15.6502 12.71 17.2402 13.91 18.4502L17.5 22.0002L21.1 18.4502C22.3 17.2402 22.24 15.6502 21.29 14.7102V14.7002Z"/>

    </svg>
  );
}
