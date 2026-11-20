import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShipIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 10.189V14"/>
      <path d="M12 2V5"/>
      <path d="M19 13V7C19 6.46957 18.7893 5.96086 18.4142 5.58579C18.0391 5.21071 17.5304 5 17 5H7C6.46957 5 5.96086 5.21071 5.58579 5.58579C5.21071 5.96086 5 6.46957 5 7V13"/>
      <path d="M19.38 20.0002C20.4557 18.1848 21.0158 16.1103 21 14.0002L12.812 10.3612C12.5564 10.2476 12.2797 10.189 12 10.189C11.7203 10.189 11.4437 10.2476 11.188 10.3612L3.00001 14.0002C2.95372 16.8439 3.95373 19.6055 5.81001 21.7602"/>
      <path d="M2 21C2.6 21.5 3.2 22 4.5 22C7 22 7 20 9.5 20C10.8 20 11.4 20.5 12 21C12.6 21.5 13.2 22 14.5 22C17 22 17 20 19.5 20C20.8 20 21.4 20.5 22 21"/>

    </svg>
  );
}
