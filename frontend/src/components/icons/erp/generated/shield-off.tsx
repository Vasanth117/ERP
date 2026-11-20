import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShieldOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L22 22"/>
      <path d="M5 5C4.73478 5 4.48043 5.10536 4.29289 5.29289C4.10536 5.48043 4 5.73478 4 6V13C4 18 7.5 20.5 11.67 21.94C11.8855 22.0203 12.1222 22.0238 12.34 21.95C14.69 21.13 16.82 19.98 18.24 18.24"/>
      <path d="M9.30902 3.65196C9.99549 3.25807 10.6422 2.79859 11.24 2.27996C11.4519 2.09896 11.7214 1.99951 12 1.99951C12.2787 1.99951 12.5482 2.09896 12.76 2.27996C14.51 3.80996 17 4.99996 19 4.99996C19.2652 4.99996 19.5196 5.10532 19.7071 5.29285C19.8947 5.48039 20 5.73474 20 5.99996V13C20.0007 13.4226 19.974 13.8448 19.92 14.264"/>

    </svg>
  );
}
