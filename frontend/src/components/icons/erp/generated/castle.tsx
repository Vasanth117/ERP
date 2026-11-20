import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CastleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 20V11H2V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H20C20.5304 22 21.0391 21.7893 21.4142 21.4142C21.7893 21.0391 22 20.5304 22 20Z"/>
      <path d="M18 11V4H6V11"/>
      <path d="M15 22V18C15 17.2044 14.6839 16.4413 14.1213 15.8787C13.5587 15.3161 12.7956 15 12 15C11.2044 15 10.4413 15.3161 9.87868 15.8787C9.31607 16.4413 9 17.2044 9 18V22"/>
      <path d="M22 11V9"/>
      <path d="M2 11V9"/>
      <path d="M6 4V2"/>
      <path d="M18 4V2"/>
      <path d="M10 4V2"/>
      <path d="M14 4V2"/>

    </svg>
  );
}
