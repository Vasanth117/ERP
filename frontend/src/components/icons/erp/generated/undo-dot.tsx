import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UndoDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 16.9996C20.9984 15.2629 20.4944 13.5638 19.5487 12.1072C18.6031 10.6505 17.2562 9.49858 15.6705 8.79031C14.0848 8.08203 12.3281 7.84766 10.6121 8.11547C8.89623 8.38328 7.29445 9.14183 6 10.2996L3 12.9996"/>
      <path d="M3 7V13H9"/>
      <path d="M11 17C11 17.2652 11.1054 17.5196 11.2929 17.7071C11.4804 17.8946 11.7348 18 12 18C12.2652 18 12.5196 17.8946 12.7071 17.7071C12.8946 17.5196 13 17.2652 13 17C13 16.7348 12.8946 16.4804 12.7071 16.2929C12.5196 16.1054 12.2652 16 12 16C11.7348 16 11.4804 16.1054 11.2929 16.2929C11.1054 16.4804 11 16.7348 11 17Z"/>

    </svg>
  );
}
