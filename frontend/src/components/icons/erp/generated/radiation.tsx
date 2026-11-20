import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RadiationIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 12H12.01"/>
      <path d="M7.49999 4.20013C7.19999 3.70013 6.59999 3.50013 6.19999 3.80013C3.89999 5.50013 2.29999 8.10013 1.99999 11.0001C1.89999 11.5001 2.39999 12.0001 2.99999 12.0001H7.99999C7.99999 10.5001 8.79999 9.20013 9.99999 8.60013C8.89999 6.70013 7.99999 5.10013 7.49999 4.20013Z"/>
      <path d="M21 12.0002C21.6 12.0002 22 11.6002 22 11.0002C21.7 8.1002 20.2 5.5002 17.9 3.9002C17.5 3.6002 16.8 3.7002 16.6 4.2002C16 5.1002 15.1 6.7002 14 8.5002C15.2 9.2002 16 10.5002 16 12.0002H21Z"/>
      <path d="M7.49999 19.8C7.19999 20.3 7.39999 20.9 7.89999 21.1C10.5 22.3 13.5 22.3 16.1 21.1C16.6 20.9 16.8 20.3 16.5 19.8C16 18.9 15.1 17.3 14 15.5C12.8 16.2 11.2 16.2 9.99999 15.5C8.89999 17.3 7.99999 18.9 7.49999 19.8Z"/>

    </svg>
  );
}
