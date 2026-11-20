import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SunMoonIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 8C11.4984 8.5362 11.2249 9.24634 11.2371 9.98047C11.2493 10.7146 11.5464 11.4152 12.0656 11.9344C12.5848 12.4536 13.2854 12.7507 14.0195 12.7629C14.7537 12.7751 15.4638 12.5016 16 12C16 12.7911 15.7654 13.5645 15.3259 14.2223C14.8864 14.8801 14.2616 15.3928 13.5307 15.6955C12.7998 15.9983 11.9956 16.0775 11.2196 15.9231C10.4437 15.7688 9.73098 15.3878 9.17157 14.8284C8.61216 14.269 8.2312 13.5563 8.07686 12.7804C7.92252 12.0044 8.00173 11.2002 8.30448 10.4693C8.60723 9.73836 9.11993 9.11365 9.77772 8.67412C10.4355 8.2346 11.2089 8 12 8Z"/>
      <path d="M12 2V4"/>
      <path d="M12 20V22"/>
      <path d="M4.89999 4.90039L6.29999 6.30039"/>
      <path d="M17.7 17.7002L19.1 19.1002"/>
      <path d="M2 12H4"/>
      <path d="M20 12H22"/>
      <path d="M6.29999 17.7002L4.89999 19.1002"/>
      <path d="M19.1 4.90039L17.7 6.30039"/>

    </svg>
  );
}
