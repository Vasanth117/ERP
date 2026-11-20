import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BluetoothSearchingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 7L17 17L12 22V2L17 7L7 17"/>
      <path d="M20.83 14.8299C21.2019 14.4584 21.4969 14.0173 21.6982 13.5317C21.8995 13.0461 22.0031 12.5256 22.0031 11.9999C22.0031 11.4743 21.8995 10.9538 21.6982 10.4682C21.4969 9.98257 21.2019 9.54141 20.83 9.16992"/>
      <path d="M18 12H18.01"/>

    </svg>
  );
}
