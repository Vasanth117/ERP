import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PianoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.5 7.99972C17.1 7.99972 15.9 7.19972 15.3 5.99972C14.732 4.42436 13.6081 3.11072 12.1396 2.30574C10.6712 1.50076 8.95925 1.25987 7.32565 1.62835C5.69206 1.99682 4.24931 2.9493 3.2686 4.30673C2.28789 5.66416 1.83677 7.33306 2.00002 8.99972V19.9997C2.00002 20.5301 2.21074 21.0389 2.58581 21.4139C2.96088 21.789 3.46959 21.9997 4.00002 21.9997H20C20.5305 21.9997 21.0392 21.789 21.4142 21.4139C21.7893 21.0389 22 20.5301 22 19.9997V11.4997C22 9.59972 20.4 7.99972 18.5 7.99972Z"/>
      <path d="M2 14H22"/>
      <path d="M6 14V18"/>
      <path d="M10 14V18"/>
      <path d="M14 14V18"/>
      <path d="M18 14V18"/>

    </svg>
  );
}
