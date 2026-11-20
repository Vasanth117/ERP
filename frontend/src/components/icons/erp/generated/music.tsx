import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MusicIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 18V5L21 3V16"/>
      <path d="M3 18C3 18.7956 3.31607 19.5587 3.87868 20.1213C4.44129 20.6839 5.20435 21 6 21C6.79565 21 7.55871 20.6839 8.12132 20.1213C8.68393 19.5587 9 18.7956 9 18C9 17.2044 8.68393 16.4413 8.12132 15.8787C7.55871 15.3161 6.79565 15 6 15C5.20435 15 4.44129 15.3161 3.87868 15.8787C3.31607 16.4413 3 17.2044 3 18Z"/>
      <path d="M15 16C15 16.7956 15.3161 17.5587 15.8787 18.1213C16.4413 18.6839 17.2044 19 18 19C18.7956 19 19.5587 18.6839 20.1213 18.1213C20.6839 17.5587 21 16.7956 21 16C21 15.2044 20.6839 14.4413 20.1213 13.8787C19.5587 13.3161 18.7956 13 18 13C17.2044 13 16.4413 13.3161 15.8787 13.8787C15.3161 14.4413 15 15.2044 15 16Z"/>

    </svg>
  );
}
