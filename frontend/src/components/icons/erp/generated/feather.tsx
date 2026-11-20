import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FeatherIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12.67 18.9995C12.9331 18.9995 13.1936 18.9475 13.4366 18.8466C13.6796 18.7457 13.9003 18.5979 14.086 18.4115L20.24 12.2395C21.3658 11.1137 21.9983 9.58673 21.9983 7.99455C21.9983 6.40236 21.3658 4.87539 20.24 3.74955C19.1142 2.6237 17.5872 1.99121 15.995 1.99121C14.4028 1.99121 12.8758 2.6237 11.75 3.74955L5.586 9.91355C5.2109 10.2885 5.00011 10.7972 5 11.3275V17.9995C5 18.2648 5.10536 18.5191 5.29289 18.7067C5.48043 18.8942 5.73478 18.9995 6 18.9995H12.67Z"/>
      <path d="M16 8L2 22"/>
      <path d="M17.5 15H9"/>

    </svg>
  );
}
