import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MilkOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2H16"/>
      <path d="M9 2V3.343M15 2V4.789C15 5.57879 15.2338 6.3509 15.672 7.008L16.328 7.992C16.7663 8.64939 17.0002 9.42187 17 10.212V11.343M7.8 7.8L7.672 7.992C7.23366 8.64939 6.99982 9.42187 7 10.212V20C7 20.5304 7.21071 21.0391 7.58579 21.4142C7.96086 21.7893 8.46957 22 9 22H15C15.5304 22 16.0391 21.7893 16.4142 21.4142C16.7893 21.0391 17 20.5304 17 20V17"/>
      <path d="M7 14.9996C7.79175 14.6679 8.64158 14.4971 9.5 14.4971C10.3584 14.4971 11.2083 14.6679 12 14.9996C13.0842 15.4539 14.2717 15.6042 15.435 15.4346"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
