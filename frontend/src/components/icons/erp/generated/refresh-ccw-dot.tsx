import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RefreshCcwDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 2V8H9"/>
      <path d="M21 11.9996C20.9984 10.2629 20.4944 8.5638 19.5487 7.10715C18.6031 5.65051 17.2562 4.49858 15.6705 3.79031C14.0848 3.08203 12.3281 2.84766 10.6121 3.11547C8.89623 3.38328 7.29445 4.14183 6 5.29962L3 7.99962"/>
      <path d="M21 22V16H15"/>
      <path d="M3 12C3.00158 13.7367 3.5056 15.4358 4.45125 16.8925C5.39691 18.3491 6.74382 19.501 8.32951 20.2093C9.9152 20.9176 11.6719 21.152 13.3879 20.8841C15.1038 20.6163 16.7056 19.8578 18 18.7L21 16"/>
      <path d="M11 12C11 12.2652 11.1054 12.5196 11.2929 12.7071C11.4804 12.8946 11.7348 13 12 13C12.2652 13 12.5196 12.8946 12.7071 12.7071C12.8946 12.5196 13 12.2652 13 12C13 11.7348 12.8946 11.4804 12.7071 11.2929C12.5196 11.1054 12.2652 11 12 11C11.7348 11 11.4804 11.1054 11.2929 11.2929C11.1054 11.4804 11 11.7348 11 12Z"/>

    </svg>
  );
}
