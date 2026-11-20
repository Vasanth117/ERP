import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L22 22"/>
      <path d="M5.782 5.78223C4.38827 6.50286 3.27705 7.67084 2.6267 9.09872C1.97634 10.5266 1.82455 12.1316 2.1957 13.6561C2.56684 15.1805 3.43939 16.5361 4.67332 17.5053C5.90724 18.4744 7.43099 19.0009 9 19.0002H17.5C17.9428 19.0005 18.3832 18.9355 18.807 18.8072"/>
      <path d="M21.532 16.4998C21.8724 15.8137 22.0321 15.052 21.9958 14.2869C21.9596 13.5218 21.7287 12.7786 21.3249 12.1277C20.9212 11.4769 20.3579 10.9398 19.6886 10.5674C19.0193 10.195 18.2659 9.99968 17.5 9.99982H15.71C15.3275 8.7191 14.5867 7.57447 13.575 6.70096C12.5632 5.82745 11.3228 5.26149 10 5.06982"/>

    </svg>
  );
}
