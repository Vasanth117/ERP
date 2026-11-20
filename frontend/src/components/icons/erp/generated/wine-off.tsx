import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WineOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 22H16"/>
      <path d="M7 10H10M17 10H15.657"/>
      <path d="M12 15V22"/>
      <path d="M7.307 7.307C7.10601 8.19066 7.00306 9.09378 7 10C7.00004 10.8671 7.22557 11.7192 7.65443 12.4728C8.08329 13.2264 8.70075 13.8555 9.44619 14.2984C10.1916 14.7412 11.0394 14.9826 11.9063 14.9989C12.7733 15.0151 13.6295 14.8056 14.391 14.391M8.638 2.981C8.75 2.668 8.872 2.34 9 2H15C16.5 6 17 8 17 10C17 10.407 16.95 10.809 16.855 11.198"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
