import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CupSodaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 8L7.75 20.28C7.81792 20.7606 8.05827 21.2 8.42624 21.5165C8.79421 21.8329 9.26469 22.0048 9.75 22H14.29C14.7753 22.0048 15.2458 21.8329 15.6138 21.5165C15.9817 21.2 16.2221 20.7606 16.29 20.28L18 8"/>
      <path d="M5 8H19"/>
      <path d="M7 14.9996C7.79175 14.6679 8.64158 14.4971 9.5 14.4971C10.3584 14.4971 11.2083 14.6679 12 14.9996C12.7917 15.3313 13.6416 15.5021 14.5 15.5021C15.3584 15.5021 16.2083 15.3313 17 14.9996"/>
      <path d="M12 8L13 2H15"/>

    </svg>
  );
}
