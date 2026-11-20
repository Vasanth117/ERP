import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CroissantIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4.60001 13.1096L10.39 9.89959C12.28 8.84959 15.18 11.6796 14.1 13.6096L10.88 19.4196C8.80001 23.1596 0.790006 15.2296 4.60001 13.1096Z"/>
      <path d="M10.5 9.5L9.5 7.21C9.2 6.48 8.8 6 8 6H4.5C2.79 6 2 6.5 2 8.5C2.08384 10.2938 2.7912 12.002 4 13.33"/>
      <path d="M8 6C8 4.45 8.24 2 6 2C4 2 3.5 4.17 3.5 6"/>
      <path d="M14.5 13.5L16.79 14.5C17.52 14.8 18 15.2 18 16V19.5C18 21.21 17.5 22 15.5 22C13.7062 21.9162 11.998 21.2088 10.67 20"/>
      <path d="M18 15.9997C19.55 15.9997 22 15.7597 22 17.9997C22 19.9997 19.83 20.4997 18 20.4997"/>

    </svg>
  );
}
