import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BombIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 13C2 15.3869 2.94821 17.6761 4.63604 19.364C6.32387 21.0518 8.61305 22 11 22C13.3869 22 15.6761 21.0518 17.364 19.364C19.0518 17.6761 20 15.3869 20 13C20 10.6131 19.0518 8.32387 17.364 6.63604C15.6761 4.94821 13.3869 4 11 4C8.61305 4 6.32387 4.94821 4.63604 6.63604C2.94821 8.32387 2 10.6131 2 13Z"/>
      <path d="M14.35 4.6498L16.3 2.6998C16.7516 2.25036 17.3628 1.99805 18 1.99805C18.6371 1.99805 19.2484 2.25036 19.7 2.6998L21.3 4.2998C21.5237 4.52277 21.7012 4.78771 21.8224 5.07944C21.9435 5.37116 22.0059 5.68393 22.0059 5.9998C22.0059 6.31568 21.9435 6.62844 21.8224 6.92017C21.7012 7.21189 21.5237 7.47683 21.3 7.6998L19.35 9.6498"/>
      <path d="M22 2L20.5 3.5"/>

    </svg>
  );
}
