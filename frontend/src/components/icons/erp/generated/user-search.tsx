import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UserSearchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 7C6 8.06087 6.42143 9.07828 7.17157 9.82843C7.92172 10.5786 8.93913 11 10 11C11.0609 11 12.0783 10.5786 12.8284 9.82843C13.5786 9.07828 14 8.06087 14 7C14 5.93913 13.5786 4.92172 12.8284 4.17157C12.0783 3.42143 11.0609 3 10 3C8.93913 3 7.92172 3.42143 7.17157 4.17157C6.42143 4.92172 6 5.93913 6 7Z"/>
      <path d="M10.3 15H7C5.93913 15 4.92172 15.4214 4.17157 16.1716C3.42143 16.9217 3 17.9391 3 19V21"/>
      <path d="M14 17C14 17.7956 14.3161 18.5587 14.8787 19.1213C15.4413 19.6839 16.2044 20 17 20C17.7956 20 18.5587 19.6839 19.1213 19.1213C19.6839 18.5587 20 17.7956 20 17C20 16.2044 19.6839 15.4413 19.1213 14.8787C18.5587 14.3161 17.7956 14 17 14C16.2044 14 15.4413 14.3161 14.8787 14.8787C14.3161 15.4413 14 16.2044 14 17Z"/>
      <path d="M21 21L19.1 19.1"/>

    </svg>
  );
}
