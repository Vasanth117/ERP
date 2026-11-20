import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TurtleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 10L14 14V17C14 17.2652 14.1054 17.5196 14.2929 17.7071C14.4804 17.8946 14.7348 18 15 18H17C17.2652 18 17.5196 17.8946 17.7071 17.7071C17.8946 17.5196 18 17.2652 18 17V14C18 11.8783 17.1571 9.84344 15.6569 8.34315C14.1566 6.84285 12.1217 6 10 6C7.87827 6 5.84344 6.84285 4.34315 8.34315C2.84285 9.84344 2 11.8783 2 14V17C2 17.2652 2.10536 17.5196 2.29289 17.7071C2.48043 17.8946 2.73478 18 3 18H5C5.26522 18 5.51957 17.8946 5.70711 17.7071C5.89464 17.5196 6 17.2652 6 17V14L8 10H12Z"/>
      <path d="M4.82 7.90039L8 10.0004"/>
      <path d="M15.18 7.90039L12 10.0004"/>
      <path d="M16.93 10H20C20.5304 10 21.0391 10.2107 21.4142 10.5858C21.7893 10.9609 22 11.4696 22 12C22 12.5304 21.7893 13.0391 21.4142 13.4142C21.0391 13.7893 20.5304 14 20 14H2"/>

    </svg>
  );
}
