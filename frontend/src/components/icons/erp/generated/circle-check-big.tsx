import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleCheckBigIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21.801 10.0005C22.2577 12.2418 21.9322 14.5719 20.8788 16.6023C19.8255 18.6326 18.1079 20.2405 16.0125 21.1578C13.9171 22.0751 11.5706 22.2463 9.36428 21.6428C7.15795 21.0394 5.22517 19.6979 3.88825 17.8419C2.55134 15.9859 1.8911 13.7277 2.01764 11.4439C2.14418 9.16001 3.04986 6.98857 4.58363 5.29165C6.1174 3.59473 8.18656 2.47491 10.446 2.11893C12.7055 1.76295 15.0188 2.19234 17 3.33548"/>
      <path d="M9 11L12 14L22 4"/>

    </svg>
  );
}
