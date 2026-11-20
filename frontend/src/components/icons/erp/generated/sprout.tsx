import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SproutIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 20H17"/>
      <path d="M10 20C15.5 17.5 10.8 13.6 13 10"/>
      <path d="M9.5 9.3996C10.6 10.1996 11.3 11.5996 11.8 13.0996C9.8 13.4996 8.3 13.4996 7 12.7996C5.8 12.1996 4.7 10.8996 4 8.59961C6.8 8.09961 8.4 8.5996 9.5 9.3996Z"/>
      <path d="M14.1 6C13.3376 7.19156 12.9541 8.58615 13 10C14.9 9.9 16.3 9.4 17.3 8.6C18.3 7.6 18.9 6.3 19 4C16.3 4.1 15 5 14.1 6Z"/>

    </svg>
  );
}
