import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlarmClockOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6.87001 6.87012C6.00764 7.57885 5.30314 8.4602 4.80179 9.45751C4.30044 10.4548 4.01335 11.546 3.95896 12.6609C3.90458 13.7758 4.08412 14.8898 4.48602 15.9311C4.88793 16.9725 5.50331 17.9182 6.29261 18.7075C7.0819 19.4968 8.02764 20.1122 9.069 20.5141C10.1104 20.916 11.2243 21.0955 12.3392 21.0412C13.4541 20.9868 14.5453 20.6997 15.5426 20.1983C16.5399 19.697 17.4213 18.9925 18.13 18.1301"/>
      <path d="M19.9 14.2499C20.0968 13.0035 19.996 11.7281 19.6058 10.5281C19.2156 9.32808 18.5471 8.23738 17.6548 7.3451C16.7625 6.45282 15.6718 5.78427 14.4718 5.39406C13.2717 5.00385 11.9964 4.90304 10.75 5.09989"/>
      <path d="M22 6L19 3"/>
      <path d="M6.26 18.6699L4 20.9999"/>
      <path d="M2 2L22 22"/>
      <path d="M4 4L2 6"/>

    </svg>
  );
}
