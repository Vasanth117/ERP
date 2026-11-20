import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PentagonIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10.8301 2.37989C11.1707 2.13418 11.5801 2.00195 12.0001 2.00195C12.4201 2.00195 12.8294 2.13418 13.1701 2.37989L21.1701 8.11989C21.5152 8.36854 21.7721 8.72077 21.9034 9.1254C22.0346 9.53002 22.0335 9.96596 21.9001 10.3699L18.8601 19.6299C18.7276 20.029 18.4727 20.3762 18.1316 20.6221C17.7905 20.8681 17.3806 21.0003 16.9601 20.9999H7.04006C6.61954 21.0003 6.2096 20.8681 5.86851 20.6221C5.52742 20.3762 5.27252 20.029 5.14006 19.6299L2.10006 10.3699C1.96664 9.96596 1.96549 9.53002 2.09677 9.1254C2.22805 8.72077 2.48492 8.36854 2.83006 8.11989L10.8301 2.37989Z"/>

    </svg>
  );
}
