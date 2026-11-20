import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BugOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 7.13V6C14.9995 5.40461 14.8219 4.82282 14.4897 4.32871C14.1575 3.8346 13.6858 3.4505 13.1346 3.22532C12.5835 3.00013 11.9778 2.94404 11.3946 3.06419C10.8115 3.18434 10.2773 3.47529 9.86 3.9L8 2"/>
      <path d="M14.12 3.88L16 2"/>
      <path d="M22 13H18V11C18 9.93913 17.5786 8.92172 16.8284 8.17157C16.0783 7.42143 15.0609 7 14 7H12.7"/>
      <path d="M20.97 5C20.97 7.1 19.37 8.8 17.47 9"/>
      <path d="M2 2L22 22"/>
      <path d="M7.7 7.7002C7.17105 8.07192 6.74008 8.56632 6.44401 9.14105C6.14794 9.71578 5.99559 10.3537 6 11.0002V14.0002C5.99601 15.3114 6.42168 16.5879 7.21189 17.6343C8.00211 18.6807 9.11336 19.4394 10.3757 19.7944C11.6379 20.1494 12.9818 20.0811 14.2016 19.6C15.4214 19.1188 16.45 18.2513 17.13 17.1302"/>
      <path d="M12 20V12"/>
      <path d="M6 13H2"/>
      <path d="M3 21C3 18.9 4.7 17.1 6.8 17"/>

    </svg>
  );
}
