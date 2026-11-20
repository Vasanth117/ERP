import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LaughIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12C22 9.34784 20.9464 6.8043 19.0711 4.92893C17.1957 3.05357 14.6522 2 12 2C9.34784 2 6.8043 3.05357 4.92893 4.92893C3.05357 6.8043 2 9.34784 2 12Z"/>
      <path d="M18 13C17.7614 14.4124 17.0254 15.6929 15.9249 16.6099C14.8245 17.5269 13.4323 18.02 12 18C10.5677 18.02 9.1755 17.5269 8.07507 16.6099C6.97464 15.6929 6.2386 14.4124 6 13H18Z"/>
      <path d="M9 9H9.01"/>
      <path d="M15 9H15.01"/>

    </svg>
  );
}
