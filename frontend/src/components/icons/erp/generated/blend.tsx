import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BlendIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 9C2 10.8565 2.7375 12.637 4.05025 13.9497C5.36301 15.2625 7.14348 16 9 16C10.8565 16 12.637 15.2625 13.9497 13.9497C15.2625 12.637 16 10.8565 16 9C16 7.14348 15.2625 5.36301 13.9497 4.05025C12.637 2.7375 10.8565 2 9 2C7.14348 2 5.36301 2.7375 4.05025 4.05025C2.7375 5.36301 2 7.14348 2 9Z"/>
      <path d="M8 15C8 16.8565 8.7375 18.637 10.0503 19.9497C11.363 21.2625 13.1435 22 15 22C16.8565 22 18.637 21.2625 19.9497 19.9497C21.2625 18.637 22 16.8565 22 15C22 13.1435 21.2625 11.363 19.9497 10.0503C18.637 8.7375 16.8565 8 15 8C13.1435 8 11.363 8.7375 10.0503 10.0503C8.7375 11.363 8 13.1435 8 15Z"/>

    </svg>
  );
}
