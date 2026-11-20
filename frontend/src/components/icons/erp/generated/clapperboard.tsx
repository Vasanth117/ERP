import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ClapperboardIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20.2 5.99995L3.00001 11L2.10001 8.59995C1.80001 7.49995 2.40001 6.39995 3.40001 6.09995L16.9 2.09995C18 1.79995 19.1 2.39995 19.4 3.39995L20.2 5.99995Z"/>
      <path d="M6.20001 5.2998L9.30001 9.1998"/>
      <path d="M12.4 3.40039L15.5 7.40039"/>
      <path d="M3 11H21V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V11Z"/>

    </svg>
  );
}
