import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CuboidIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21.12 6.39966L15.07 2.33966C14.7515 2.12333 14.3773 2.00354 13.9924 1.99467C13.6074 1.9858 13.2281 2.08823 12.9 2.28966L2.95 8.40966C2.65992 8.5886 2.42038 8.8387 2.25411 9.13622C2.08785 9.43375 2.00038 9.76883 2 10.1097V15.9297C1.99951 16.2573 2.0795 16.58 2.23294 16.8694C2.38639 17.1589 2.60858 17.4062 2.88 17.5897L8.93 21.6597C9.24852 21.876 9.6227 21.9958 10.0076 22.0047C10.3926 22.0135 10.7719 21.9111 11.1 21.7097L21.05 15.5897C21.3401 15.4107 21.5796 15.1606 21.7459 14.8631C21.9122 14.5656 21.9996 14.2305 22 13.8897V8.05966C22.0005 7.73206 21.9205 7.40934 21.7671 7.11989C21.6136 6.83044 21.3914 6.58312 21.12 6.39966Z"/>
      <path d="M10 22.0004V14.0004L2.25 9.15039"/>
      <path d="M10 13.9999L21.77 7.12988"/>

    </svg>
  );
}
