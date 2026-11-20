import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PopsicleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.6 14.3998C19.4 13.5998 19.4 12.3998 18.6 11.5998L10.5 3.49975C9.55847 2.55824 8.2815 2.0293 6.94999 2.0293C5.61848 2.0293 4.34151 2.55824 3.39999 3.49975C2.45847 4.44127 1.92953 5.71825 1.92953 7.04976C1.92953 8.38126 2.45847 9.65824 3.39999 10.5998L11.5 18.6998C12.4 19.3998 13.6 19.3998 14.4 18.5998L18.6 14.3998Z"/>
      <path d="M22 22L16.5 16.5"/>

    </svg>
  );
}
