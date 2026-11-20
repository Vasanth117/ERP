import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleArrowOutDownLeftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12C2 10.0222 2.58649 8.08879 3.6853 6.4443C4.78412 4.79981 6.3459 3.51809 8.17317 2.76121C10.0004 2.00433 12.0111 1.8063 13.9509 2.19215C15.8907 2.578 17.6725 3.53041 19.0711 4.92894C20.4696 6.32746 21.422 8.10929 21.8079 10.0491C22.1937 11.9889 21.9957 13.9996 21.2388 15.8268C20.4819 17.6541 19.2002 19.2159 17.5557 20.3147C15.9112 21.4135 13.9778 22 12 22"/>
      <path d="M2 22L12 12"/>
      <path d="M8 22H2V16"/>

    </svg>
  );
}
