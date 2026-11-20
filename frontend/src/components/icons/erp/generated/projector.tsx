import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ProjectorIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 7L3 5"/>
      <path d="M9 6V3"/>
      <path d="M13 7L15 5"/>
      <path d="M6 13C6 13.7956 6.31607 14.5587 6.87868 15.1213C7.44129 15.6839 8.20435 16 9 16C9.79565 16 10.5587 15.6839 11.1213 15.1213C11.6839 14.5587 12 13.7956 12 13C12 12.2044 11.6839 11.4413 11.1213 10.8787C10.5587 10.3161 9.79565 10 9 10C8.20435 10 7.44129 10.3161 6.87868 10.8787C6.31607 11.4413 6 12.2044 6 13Z"/>
      <path d="M11.83 12H20C20.5304 12 21.0391 12.2107 21.4142 12.5858C21.7893 12.9609 22 13.4696 22 14V18C22 18.5304 21.7893 19.0391 21.4142 19.4142C21.0391 19.7893 20.5304 20 20 20H4C3.46957 20 2.96086 19.7893 2.58579 19.4142C2.21071 19.0391 2 18.5304 2 18V14C2 13.4696 2.21071 12.9609 2.58579 12.5858C2.96086 12.2107 3.46957 12 4 12H6.17"/>
      <path d="M16 16H18"/>

    </svg>
  );
}
