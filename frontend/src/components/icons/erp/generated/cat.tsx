import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CatIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 4.99978C12.67 4.99978 13.35 5.08978 14 5.25978C15.78 3.25978 19.03 2.41978 20.42 2.99978C21.82 3.57978 20 9.99978 20 9.99978C20.57 11.0698 21 12.2398 21 13.4398C21 17.8998 16.97 20.9998 12 20.9998C7.02999 20.9998 2.99999 17.9998 2.99999 13.4398C2.99999 12.1898 3.49999 11.0398 3.99999 9.99978C3.99999 9.99978 2.10999 3.57978 3.49999 2.99978C4.88999 2.41978 8.21999 3.22978 9.99999 5.22978C10.656 5.07888 11.3268 5.00174 12 4.99978Z"/>
      <path d="M8 14V14.5"/>
      <path d="M16 14V14.5"/>
      <path d="M11.25 16.25H12.75L12 17L11.25 16.25Z"/>

    </svg>
  );
}
