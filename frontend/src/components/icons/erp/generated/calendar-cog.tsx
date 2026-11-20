import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CalendarCogIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15.2 16.9L14.3 16.5"/>
      <path d="M15.2 19.1001L14.3 19.5001"/>
      <path d="M16 2V6"/>
      <path d="M16.9 15.1998L16.5 14.2998"/>
      <path d="M16.9 20.7998L16.5 21.6998"/>
      <path d="M19.5 14.2998L19.1 15.1998"/>
      <path d="M19.5 21.6998L19.1 20.7998"/>
      <path d="M21 10.5V6C21 5.46957 20.7893 4.96086 20.4142 4.58579C20.0391 4.21071 19.5304 4 19 4H5C4.46957 4 3.96086 4.21071 3.58579 4.58579C3.21071 4.96086 3 5.46957 3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H11"/>
      <path d="M21.7001 16.5L20.8 16.9"/>
      <path d="M21.7001 19.5001L20.8 19.1001"/>
      <path d="M3 10H21"/>
      <path d="M8 2V6"/>
      <path d="M15 18C15 18.7956 15.3161 19.5587 15.8787 20.1213C16.4413 20.6839 17.2044 21 18 21C18.7956 21 19.5587 20.6839 20.1213 20.1213C20.6839 19.5587 21 18.7956 21 18C21 17.2044 20.6839 16.4413 20.1213 15.8787C19.5587 15.3161 18.7956 15 18 15C17.2044 15 16.4413 15.3161 15.8787 15.8787C15.3161 16.4413 15 17.2044 15 18Z"/>

    </svg>
  );
}
